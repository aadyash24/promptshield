#!/usr/bin/env python3
"""Score a detector on a split. Works with a model (zero-shot or fine-tuned) or a baseline.

Examples:
  python evaluate.py --baseline regex --split test            # no GPU needed
  python evaluate.py --baseline oracle --split test            # sanity check, must score 1.0
  python evaluate.py --base Qwen/Qwen2.5-1.5B-Instruct --split test              # zero-shot
  python evaluate.py --base Qwen/Qwen2.5-1.5B-Instruct --adapter out/qwen15 --split test   # fine-tuned
Results go to results/<name>/ : metrics.json, report.md, errors.jsonl
"""
import argparse
import json
import time
from pathlib import Path

from metrics import parse_findings, report_markdown, score

HERE = Path(__file__).parent


def load_split(split: str, limit: int | None):
    if split == "handwritten":  # built on the fly so teammates' prompt files are always included
        from handwritten import build
        rows = build()
        return rows[:limit] if limit else rows
    rows = [json.loads(line) for line in open(HERE / "data" / f"{split}.jsonl", encoding="utf-8")]
    return rows[:limit] if limit else rows


def baseline_predictor(name: str, rows):
    if name == "oracle":
        return [[{"text": f["text"], "category": f["category"], "tier": f["tier"]} for f in r["findings"]] for r in rows], [True] * len(rows)
    if name == "empty":
        return [[] for _ in rows], [True] * len(rows)
    if name == "regex":
        from baseline_regex import predict
        return [predict(r["prompt"]) for r in rows], [True] * len(rows)
    raise SystemExit(f"unknown baseline {name}")


def model_predictor(base: str, adapter: str | None, rows, batch_size: int, max_new_tokens: int):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    from prompt import build_messages

    tok = AutoTokenizer.from_pretrained(adapter or base)
    tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(base)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(torch.float16 if device == "cuda" else torch.float32)
    if adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, adapter)
    model.to(device).eval()

    preds, valid = [], []
    for i in range(0, len(rows), batch_size):
        chunk = rows[i:i + batch_size]
        texts = [tok.apply_chat_template(build_messages(r["prompt"]), tokenize=False, add_generation_prompt=True) for r in chunk]
        enc = tok(texts, return_tensors="pt", padding=True, add_special_tokens=False).to(device)
        with torch.no_grad():
            out = model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False, pad_token_id=tok.pad_token_id)
        for j in range(len(chunk)):
            raw = tok.decode(out[j][enc["input_ids"].shape[1]:], skip_special_tokens=True)
            findings, ok = parse_findings(raw)
            preds.append(findings)
            valid.append(ok)
        print(f"  {min(i + batch_size, len(rows))}/{len(rows)}", flush=True)
    return preds, valid


def token_predictor(path: str, rows, batch_size: int):
    from token_model import TokenDetector

    det = TokenDetector(path)
    preds = []
    for i in range(0, len(rows), 256):
        preds += det.predict([r["prompt"] for r in rows[i:i + 256]], batch_size)
        print(f"  {min(i + 256, len(rows))}/{len(rows)}", flush=True)
    return preds, [True] * len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test", choices=["train", "val", "test", "handwritten"])
    ap.add_argument("--limit", type=int)
    ap.add_argument("--baseline", choices=["oracle", "empty", "regex"])
    ap.add_argument("--token-model", help="folder of a token classifier trained with train_token.py")
    ap.add_argument("--base", help="HF model id of the base model")
    ap.add_argument("--adapter", help="path to a LoRA adapter folder from train_lora.py")
    ap.add_argument("--name", help="results folder name")
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--max-new-tokens", type=int, default=256)
    args = ap.parse_args()
    if not args.baseline and not args.base and not args.token_model:
        raise SystemExit("give --baseline, --base, or --token-model")

    rows = load_split(args.split, args.limit)
    if args.token_model:
        label = f"token-{Path(args.token_model).name}"
    else:
        label = args.baseline or (f"{args.base.split('/')[-1]}{'+' + Path(args.adapter).name if args.adapter else ' (zero-shot)'}")
    name = args.name or f"{label.replace(' ', '_').replace('(', '').replace(')', '')}-{args.split}"

    t0 = time.time()
    if args.baseline:
        preds, valid = baseline_predictor(args.baseline, rows)
    elif args.token_model:
        preds, valid = token_predictor(args.token_model, rows, args.batch_size)
    else:
        preds, valid = model_predictor(args.base, args.adapter, rows, args.batch_size, args.max_new_tokens)
    secs = time.time() - t0

    golds = [r["findings"] for r in rows]
    m = score([r["prompt"] for r in rows], golds, preds)
    m["valid_json_rate"] = round(sum(valid) / len(valid), 4)
    m["seconds"] = round(secs, 1)
    m["seconds_per_prompt"] = round(secs / len(rows), 3)

    out = HERE / "results" / name
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(m, indent=2), encoding="utf-8")
    report = report_markdown(f"{label} on {args.split}", m)
    report += f"\n\nValid output: {m['valid_json_rate']:.3f}. Time: {m['seconds_per_prompt']} s per prompt.\n"
    (out / "report.md").write_text(report, encoding="utf-8")
    with open(out / "errors.jsonl", "w", encoding="utf-8") as fh:
        for r, p in zip(rows, preds):
            gold_keys = {(f["text"].lower(), f["category"]) for f in r["findings"]}
            pred_keys = {(f["text"].lower(), f.get("category")) for f in p}
            if gold_keys != pred_keys:
                fh.write(json.dumps({"id": r["id"], "prompt": r["prompt"], "missed": sorted(gold_keys - pred_keys),
                                     "extra": sorted(pred_keys - gold_keys)}, ensure_ascii=False) + "\n")
    print(report)
    print(f"saved to {out}")


if __name__ == "__main__":
    main()
