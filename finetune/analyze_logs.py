#!/usr/bin/env python3
"""Summarize study logs (Nov 14 milestone): disclosure and warning rates, active vs silent.

    python analyze_logs.py                       # reads study_logs/
    python analyze_logs.py --log-dir path --csv out.csv

Definitions (per task, one row per participant and task, using the LAST send in the task):
  disclosed        the sent message still contained at least one sensitive item
  very_disclosed   the sent message contained a very sensitive (tier 2) item
  warned           a warning card was visible when the message was sent (active condition only)
  would_warn       the detector flagged something while typing. In the silent condition no card is
                   shown, so this is how often a warning WOULD have appeared.
  rewrite_applied  the participant used the safer version
Tasks are nested in participants, so the significance test works on per-participant rates.
"""
import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent


def load(log_dir: Path):
    events = []
    for f in sorted(log_dir.glob("*.jsonl")):
        events += [json.loads(line) for line in open(f, encoding="utf-8") if line.strip()]
    return events


def task_rows(events):
    by = defaultdict(list)
    for e in events:
        if e.get("task"):
            by[(e["pid"], e["task"])].append(e)
    rows = []
    for (pid, task), evs in by.items():
        sends = [e for e in evs if e["event"] == "send"]
        if not sends:
            continue
        last = sends[-1]
        names = {e["event"] for e in evs}
        rows.append({
            "pid": pid, "cond": evs[0]["cond"], "task": task,
            "disclosed": bool(last.get("disclosed")),
            "very_disclosed": last.get("max_tier") == 2 and bool(last.get("disclosed")),
            "n_items_sent": last.get("n", 0),
            "warned": bool(last.get("warned")),
            "would_warn": "detected" in names,
            "warning_shown": "warning_shown" in names,
            "rewrite_applied": "rewrite_applied" in names,
            "warning_ignored": "warning_ignored" in names,
            "seconds": round((last.get("ms") or 0) / 1000, 1),
        })
    return rows


def rate(rows, key):
    return sum(r[key] for r in rows) / len(rows) if rows else float("nan")


def perm_test(rows, key="disclosed", n=10000, seed=1):
    """Permutation test on per-participant rates: is active different from silent?"""
    per = defaultdict(list)
    for r in rows:
        per[(r["pid"], r["cond"])].append(r[key])
    vals = [(c, sum(v) / len(v)) for (_, c), v in per.items()]
    a = [v for c, v in vals if c == "active"]
    s = [v for c, v in vals if c == "silent"]
    if len(a) < 2 or len(s) < 2:
        return None
    obs = sum(a) / len(a) - sum(s) / len(s)
    rng, labels, hits = random.Random(seed), [c for c, _ in vals], 0
    nums = [v for _, v in vals]
    for _ in range(n):
        rng.shuffle(labels)
        pa = [x for l, x in zip(labels, nums) if l == "active"]
        ps = [x for l, x in zip(labels, nums) if l == "silent"]
        if abs(sum(pa) / len(pa) - sum(ps) / len(ps)) >= abs(obs) - 1e-12:
            hits += 1
    return obs, (hits + 1) / (n + 1)


def report(rows):
    out = ["| Measure | Active | Silent |", "| --- | --- | --- |"]
    act = [r for r in rows if r["cond"] == "active"]
    sil = [r for r in rows if r["cond"] == "silent"]
    pct = lambda x: "n/a" if x != x else f"{x:.0%}"
    out.append(f"| Participants | {len({r['pid'] for r in act})} | {len({r['pid'] for r in sil})} |")
    out.append(f"| Tasks completed | {len(act)} | {len(sil)} |")
    out.append(f"| Disclosure rate (any sensitive item sent) | {pct(rate(act,'disclosed'))} | {pct(rate(sil,'disclosed'))} |")
    out.append(f"| Very sensitive disclosure rate | {pct(rate(act,'very_disclosed'))} | {pct(rate(sil,'very_disclosed'))} |")
    out.append(f"| Warning rate (card shown / would have shown) | {pct(rate(act,'warning_shown'))} | {pct(rate(sil,'would_warn'))} |")
    shown = [r for r in act if r["warning_shown"]]
    if shown:
        out.append(f"| Heeded the warning (sent clean after a warning) | {pct(1 - rate(shown,'disclosed'))} | n/a |")
        out.append(f"| Used the safer rewrite (after a warning) | {pct(rate(shown,'rewrite_applied'))} | n/a |")
        out.append(f"| Ignored the warning button (after a warning) | {pct(rate(shown,'warning_ignored'))} | n/a |")
    out.append("")
    res = perm_test(rows)
    if res:
        out.append(f"Difference in per-participant disclosure rate (active minus silent): {res[0]:+.2f}, "
                   f"permutation test p = {res[1]:.3f}")
    else:
        out.append("Not enough participants per condition for a significance test (need at least 2 each).")
    out += ["", "By task:", "", "| Task | Active disclosure | Silent disclosure |", "| --- | --- | --- |"]
    for t in sorted({r["task"] for r in rows}):
        a = [r for r in act if r["task"] == t]
        s = [r for r in sil if r["task"] == t]
        out.append(f"| {t} | {pct(rate(a,'disclosed'))} ({len(a)}) | {pct(rate(s,'disclosed'))} ({len(s)}) |")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log-dir", default=str(HERE / "study_logs"))
    ap.add_argument("--csv", help="also write one row per participant and task")
    args = ap.parse_args()
    rows = task_rows(load(Path(args.log_dir)))
    if not rows:
        raise SystemExit("no completed tasks found in the logs")
    print(report(rows))
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print(f"\nwrote {args.csv}")


if __name__ == "__main__":
    main()
