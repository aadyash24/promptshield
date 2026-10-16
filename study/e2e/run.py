#!/usr/bin/env python3
"""End-to-end check of the study flow in a real Chromium with the built extension loaded.

    npx wxt build && python study/e2e/run.py

Starts finetune/serve.py in regex-only mode (no model needed), walks two participants through
the mock chat (one lands in each condition), then checks what the logs contain.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
EXT = ROOT / ".output" / "chrome-mv3"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
MSG = "Dear bank, my card is 4539 1488 0343 6467 and my SSN is 527-61-3849. Please fix the double charge."
BASE = "http://127.0.0.1:8765"


def wait_health():
    for _ in range(60):
        try:
            urllib.request.urlopen(f"{BASE}/health", timeout=1)
            return
        except Exception:
            time.sleep(0.25)
    raise SystemExit("server did not start")


def card_visible(page):
    return page.evaluate("[...document.documentElement.children].some(e => e.tagName === 'DIV')")


def run_participant(ctx, pid, shots):
    page = ctx.new_page()
    page.goto(f"{BASE}/assign?pid={pid}")
    page.click("#start")
    page.wait_for_timeout(1500)
    page.click("#prompt")
    page.keyboard.type(MSG, delay=5)
    page.wait_for_timeout(2500)
    shown = card_visible(page)
    page.screenshot(path=str(shots / f"{pid}.png"))
    page.click("#send")
    page.wait_for_timeout(2500)
    page.close()
    return shown


def main():
    if not EXT.exists():
        sys.exit("build first: npx wxt build")
    logs = Path(tempfile.mkdtemp(prefix="pwlogs_"))
    shots = Path(tempfile.mkdtemp(prefix="pwshots_"))
    srv = subprocess.Popen([sys.executable, str(ROOT / "finetune" / "serve.py"), "--regex-only",
                            "--log-dir", str(logs), "--seed", "1"], cwd=ROOT / "finetune",
                           stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    try:
        wait_health()
        profile = tempfile.mkdtemp(prefix="pwprof_")
        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(
                profile, executable_path=CHROME, headless=False,
                args=["--headless=new", f"--disable-extensions-except={EXT}", f"--load-extension={EXT}",
                      "--no-sandbox"])
            shown = {pid: run_participant(ctx, pid, shots) for pid in ("P01", "P02")}
            ctx.close()
        assign = json.loads((logs / "assignments.json").read_text())
        print("assignments:", assign)
        ok = True
        for pid in ("P01", "P02"):
            events = [json.loads(l) for l in open(logs / f"{pid}.jsonl")]
            names = [e["event"] for e in events]
            send = next((e for e in events if e["event"] == "send"), {})
            raw = (logs / f"{pid}.jsonl").read_text()
            leaked = any(s in raw for s in ("4539", "527-61", "Dear bank"))
            print(pid, assign[pid], "card_visible=", shown[pid], names)
            print("   send:", send)
            want_card = assign[pid] == "active"
            checks = {
                "card matches condition": shown[pid] == want_card,
                "logged session_start and task_start": "session_start" in names and "task_start" in names,
                "logged detection": "detected" in names,
                "warning_shown only when active": ("warning_shown" in names) == want_card,
                "send disclosed": send.get("disclosed") is True,
                "send warned matches condition": send.get("warned") == want_card,
                "cond in every event": all(e["cond"] == assign[pid] for e in events),
                "no prompt text or values in log": not leaked,
            }
            for k, v in checks.items():
                print(("   PASS " if v else "   FAIL ") + k)
                ok &= v
        print("screenshots:", shots)
        sys.exit(0 if ok else 1)
    finally:
        srv.terminate()
        shutil.rmtree(logs, ignore_errors=True)


if __name__ == "__main__":
    main()
