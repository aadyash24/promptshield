"""Transient exact-value tracking. Only category/tier/count summaries leave this object.

A removal means a previously detected literal occurs fewer times, not that its
meaning disappeared or that the user intended privacy protection. No hashes or
text are persisted. Values are forgotten when the draft is sent/reset.
"""


class ManualEditTracker:
    def __init__(self):
        self.values = {}
        self.scans = 0

    def observe(self, text, findings):
        self.scans += 1
        for finding in findings:
            value = text[finding["start"]:finding["end"]]
            if not value:
                continue
            key = (value, finding.get("category", "SENSITIVE"), finding.get("tier", 1))
            self.values.setdefault(key, {"count": text.count(value), "removed": 0})

    def edit(self, text, source="manual"):
        changes = {}
        for (value, category, tier), state in self.values.items():
            count = text.count(value)
            delta = state["count"] - count
            if source == "manual" and delta:
                row = changes.setdefault((category, tier), {"removed": 0, "restored": 0})
                if delta > 0:
                    state["removed"] += delta
                    row["removed"] += delta
                else:
                    restored = min(state["removed"], -delta)
                    state["removed"] -= restored
                    row["restored"] += restored
            elif source != "manual":
                # Mixed automatic edits cannot be attributed confidently.
                state["removed"] = 0
            state["count"] = count
        return [{"category": c, "tier": t, **counts} for (c, t), counts in sorted(changes.items())
                if counts["removed"] or counts["restored"]]

    def summary(self):
        counts = {}
        for (_, category, tier), state in self.values.items():
            if state["removed"]:
                key = (category, tier)
                counts[key] = counts.get(key, 0) + state["removed"]
        return [{"category": c, "tier": t, "count": count} for (c, t), count in sorted(counts.items())]
