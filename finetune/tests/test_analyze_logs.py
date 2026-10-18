import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import analyze_logs as al  # noqa: E402


def write(tmp, pid, cond, tasks):
    lines = []
    for task, disclosed, warned in tasks:
        lines.append({"pid": pid, "cond": cond, "task": task, "event": "detected", "n": 1, "max_tier": 2})
        if warned:
            lines.append({"pid": pid, "cond": cond, "task": task, "event": "warning_shown", "n": 1})
        lines.append({"pid": pid, "cond": cond, "task": task, "event": "send", "n": int(disclosed),
                      "max_tier": 2 if disclosed else 0, "disclosed": disclosed, "warned": warned, "ms": 4000})
    (tmp / f"{pid}.jsonl").write_text("\n".join(json.dumps(x) for x in lines))


def test_rates_and_test(tmp_path):
    for i in range(4):  # active participants rarely disclose, silent ones always do
        write(tmp_path, f"A{i}", "active", [("bank", i == 0, True), ("rental", False, True)])
        write(tmp_path, f"S{i}", "silent", [("bank", True, False), ("rental", True, False)])
    rows = al.task_rows(al.load(tmp_path))
    act = [r for r in rows if r["cond"] == "active"]
    sil = [r for r in rows if r["cond"] == "silent"]
    assert al.rate(act, "disclosed") == 1 / 8 and al.rate(sil, "disclosed") == 1.0
    assert al.rate(sil, "would_warn") == 1.0 and al.rate(sil, "warning_shown") == 0.0
    diff, p = al.perm_test(rows)
    assert diff < 0 and p < 0.05
    assert "Disclosure rate" in al.report(rows)
