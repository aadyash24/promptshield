"""The instruction given to the model, and the exact JSON format it must return.

The SAME system prompt is used for zero-shot testing, training, and inference. Do not edit
it between those steps. It is generated from taxonomy.py so categories stay in sync.
"""
import json

from taxonomy import CATEGORIES, TIER_LABEL


def _category_line() -> str:
    parts = []
    for tier in (1, 2, 3):
        names = " ".join(c.name for c in CATEGORIES if c.tier == tier)
        parts.append(f"tier {tier} ({TIER_LABEL[tier]}): {names}")
    return "\n".join(parts)


SYSTEM_PROMPT = (
    "You are a privacy filter. Read the user's message and list every piece of sensitive personal "
    "information the writer discloses about themselves or people they know. Copy each item exactly "
    "as written. Ignore general questions, public figures, fictional characters, and example formats.\n"
    'Reply with only JSON: {"findings":[{"text":"...","category":"...","tier":N}]}, '
    'or {"findings":[]} if nothing is sensitive.\n'
    "Categories by risk tier:\n" + _category_line()
)


def build_messages(prompt: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]


def target_json(findings: list[dict]) -> str:
    """Training target. Offsets are dropped: the model copies text, code finds the position."""
    slim = [{"text": f["text"], "category": f["category"], "tier": f["tier"]} for f in findings]
    return json.dumps({"findings": slim}, ensure_ascii=False, separators=(",", ":"))
