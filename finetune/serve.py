#!/usr/bin/env python3
"""Local server for the demo and the user study. Everything stays on this computer.

    python serve.py --token-model out/tok-distilbert                       # token classifier (fast)
    python serve.py --base Qwen/Qwen3-1.7B --adapter out/adapter   # fine-tuned LLM
    python serve.py --regex-only                                              # no model, for testing

It does three jobs on http://127.0.0.1:8765 :
  POST /detect   the extension sends a prompt, gets back findings as JSON
  POST /log      the extension sends study events. Only whitelisted fields are kept.
  /mock/         the mock chat page used in the study
  /demo          the animated pipeline page, wired to the real detector (for presentations)
  /assign?pid=P01   balanced random active/silent assignment, then redirects to the mock chat

Privacy: /detect never writes the prompt anywhere. /log rejects anything that is not an
event-only record, so prompt text cannot end up in the study logs even by mistake.
"""
import argparse
import json
import random
import re
import threading
import time
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from taxonomy import BY_NAME

HERE = Path(__file__).parent
MOCK_ROOT = (HERE.parent / "study" / "mock").resolve()
DEMO_ROOT = (HERE.parent / "study" / "demo").resolve()
MAX_PROMPT = 4000

PID_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
TASK_RE = re.compile(r"^[A-Za-z0-9_-]{0,32}$")
CAT_RE = re.compile(r"^[A-Z_]{1,24}$")
EVENTS = {"session_start", "task_start", "detected", "warning_shown", "rewrite_clicked",
          "rewrite_applied", "warning_ignored", "send"}
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".json": "application/json", ".svg": "image/svg+xml"}


class Detector:
    """Wraps the fine-tuned model, or the regex baseline when no model is available."""

    def __init__(self, base=None, adapter=None, max_new_tokens=256, token_model=None):
        self.mode = "regex"
        self.lock = threading.Lock()
        self.cache: OrderedDict[str, list] = OrderedDict()
        self.max_new_tokens = max_new_tokens
        if token_model:
            self._load_token(token_model)
        elif base:
            self._load(base, adapter)

    def _load_token(self, path):
        try:
            from token_model import TokenDetector

            print(f"loading token classifier {path} ...")
            self.token = TokenDetector(path)
            self.mode = "token"
            print(f"token classifier ready on {self.token.device}")
        except Exception as err:
            print(f"WARNING: could not load the token classifier ({err}). Falling back to regex only.")

    def _load(self, base, adapter):
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            device = "cuda" if torch.cuda.is_available() else (
                "mps" if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available() else "cpu")
            dtype = torch.float16 if device != "cpu" else torch.float32
            print(f"loading {base} on {device} ...")
            self.tok = AutoTokenizer.from_pretrained(adapter or base)
            model = AutoModelForCausalLM.from_pretrained(base, torch_dtype=dtype)
            if adapter:
                from peft import PeftModel
                model = PeftModel.from_pretrained(model, adapter)
            self.model = model.to(device).eval()
            self.device, self.torch = device, torch
            self.mode = "model"
            print("model ready")
        except Exception as err:  # keep the demo alive with the rules-only detector
            print(f"WARNING: could not load the model ({err}). Falling back to regex only.")

    def detect(self, text: str) -> list[dict]:
        if text in self.cache:
            self.cache.move_to_end(text)
            return self.cache[text]
        if self.mode == "token":
            findings = self.token.predict([text])[0]
        elif self.mode == "model":
            findings = self._model_detect(text)
        else:
            from baseline_regex import predict
            findings = predict(text)
        self.cache[text] = findings
        if len(self.cache) > 256:
            self.cache.popitem(last=False)
        return findings

    def _model_detect(self, text: str) -> list[dict]:
        from metrics import parse_findings
        from prompt import chat_prompt

        with self.lock:  # one generation at a time
            chat = chat_prompt(self.tok, text)
            enc = self.tok(chat, return_tensors="pt", add_special_tokens=False).to(self.device)
            with self.torch.no_grad():
                out = self.model.generate(**enc, max_new_tokens=self.max_new_tokens, do_sample=False,
                                          pad_token_id=self.tok.pad_token_id or self.tok.eos_token_id)
            raw = self.tok.decode(out[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)
        findings, _ = parse_findings(raw)
        keep = []
        for f in findings:
            # Hallucination guard: only report text that is really in the prompt.
            if f["text"] in text and f["category"] in BY_NAME:
                keep.append({"text": f["text"], "category": f["category"], "tier": BY_NAME[f["category"]].tier})
        return keep


def clean_event(raw: dict) -> dict | None:
    """Keep only whitelisted, validated fields. Returns None to reject the record."""
    if not isinstance(raw, dict):
        return None
    pid, cond, task, event = raw.get("pid"), raw.get("cond"), raw.get("task", ""), raw.get("event")
    if not (isinstance(pid, str) and PID_RE.match(pid)):
        return None
    if cond not in ("active", "silent") or event not in EVENTS:
        return None
    if not (isinstance(task, str) and TASK_RE.match(task)):
        return None
    out = {"pid": pid, "cond": cond, "task": task, "event": event}
    n = raw.get("n")
    if isinstance(n, int) and 0 <= n <= 1000:
        out["n"] = n
    cats = raw.get("categories")
    if isinstance(cats, list) and len(cats) <= 30 and all(isinstance(c, str) and CAT_RE.match(c) for c in cats):
        out["categories"] = cats
    tier = raw.get("max_tier")
    if tier in (0, 1, 2, 3):
        out["max_tier"] = tier
    for key in ("disclosed", "warned"):
        if isinstance(raw.get(key), bool):
            out[key] = raw[key]
    ms = raw.get("ms")
    if isinstance(ms, (int, float)) and 0 <= ms < 36_000_000:
        out["ms"] = int(ms)
    return out


class Assigner:
    """Balanced random assignment to active or silent, remembered across restarts."""

    def __init__(self, log_dir: Path, seed=None):
        self.path = log_dir / "assignments.json"
        self.lock = threading.Lock()
        self.rng = random.Random(seed)
        self.data = json.loads(self.path.read_text()) if self.path.exists() else {}

    def get(self, pid: str) -> str:
        with self.lock:
            if pid not in self.data:
                a = sum(1 for c in self.data.values() if c == "active")
                s = len(self.data) - a
                self.data[pid] = "active" if a < s else "silent" if s < a else self.rng.choice(["active", "silent"])
                self.path.write_text(json.dumps(self.data, indent=2))
            return self.data[pid]

    def peek(self, pid: str):
        return self.data.get(pid)


def make_handler(detector: Detector, log_dir: Path, assigner: Assigner):
    log_lock = threading.Lock()

    class H(BaseHTTPRequestHandler):
        server_version = "PromptGuard"

        def log_message(self, *_):  # never print request bodies or URLs with prompts
            pass

        def _send(self, code, body=b"", ctype="application/json", extra=None):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _json(self, code, obj):
            self._send(code, json.dumps(obj).encode())

        def _body(self):
            n = int(self.headers.get("Content-Length") or 0)
            if n > 20000:
                return None
            try:
                return json.loads(self.rfile.read(n) or b"{}")
            except Exception:
                return None

        def do_POST(self):
            path = urlparse(self.path).path
            data = self._body()
            if path == "/detect":
                text = data.get("text") if isinstance(data, dict) else None
                if not isinstance(text, str) or not text.strip() or len(text) > MAX_PROMPT:
                    return self._json(400, {"error": "bad text"})
                return self._json(200, {"findings": detector.detect(text), "mode": detector.mode})
            if path == "/log":
                rec = clean_event(data)
                if rec is None:
                    return self._json(400, {"error": "rejected"})
                rec["t"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
                with log_lock:
                    with open(log_dir / f"{rec['pid']}.jsonl", "a", encoding="utf-8") as fh:
                        fh.write(json.dumps(rec) + "\n")
                return self._json(200, {"ok": True})
            self._json(404, {"error": "not found"})

        def do_GET(self):
            u = urlparse(self.path)
            q = parse_qs(u.query)
            if u.path == "/health":
                return self._json(200, {"ok": True, "mode": detector.mode})
            if u.path == "/cond":
                pid = (q.get("pid") or [""])[0]
                if not PID_RE.match(pid):
                    return self._json(400, {"error": "bad pid"})
                return self._json(200, {"cond": assigner.get(pid)})
            if u.path == "/assign":
                pid = (q.get("pid") or [""])[0]
                if not PID_RE.match(pid):
                    return self._send(400, b"pid must be letters, digits, - or _", "text/plain")
                assigner.get(pid)  # the condition stays hidden from the participant
                return self._send(302, b"", "text/plain", {"Location": f"/mock/?pid={pid}"})
            if u.path in ("/demo", "/demo/"):
                f = DEMO_ROOT / "index.html"
                if not f.is_file():
                    return self._send(404, b"not found", "text/plain")
                return self._send(200, f.read_bytes(), TYPES[".html"])
            if u.path.startswith("/mock"):
                rel = u.path[len("/mock"):].lstrip("/") or "index.html"
                f = (MOCK_ROOT / rel).resolve()
                if MOCK_ROOT not in f.parents and f != MOCK_ROOT or not f.is_file():
                    return self._send(404, b"not found", "text/plain")
                return self._send(200, f.read_bytes(), TYPES.get(f.suffix, "application/octet-stream"))
            self._send(404, b"not found", "text/plain")

    return H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--token-model", help="folder of a token classifier from train_token.py (fastest option)")
    ap.add_argument("--base", help="base model, e.g. Qwen/Qwen3-1.7B (or a merged model folder)")
    ap.add_argument("--adapter", help="LoRA adapter folder from train_lora.py")
    ap.add_argument("--regex-only", action="store_true", help="skip the model, use rules only")
    ap.add_argument("--log-dir", default=str(HERE / "study_logs"))
    ap.add_argument("--max-new-tokens", type=int, default=256)
    ap.add_argument("--seed", type=int, default=None, help="seed for the assignment coin flips")
    args = ap.parse_args()

    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    detector = Detector(None if args.regex_only else args.base, args.adapter, args.max_new_tokens,
                        None if args.regex_only else args.token_model)
    handler = make_handler(detector, log_dir, Assigner(log_dir, args.seed))
    srv = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"mode: {detector.mode}   logs: {log_dir}")
    print(f"mock chat: http://{args.host}:{args.port}/assign?pid=P01")
    print(f"demo page: http://{args.host}:{args.port}/demo")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
