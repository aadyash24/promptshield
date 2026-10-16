"""A deliberately simple regex baseline, so the fine-tuned model has something to beat.

It only knows structured formats. It cannot see names, conditions, income, or context, which
is exactly the gap an LLM is supposed to close.
"""
import re

from taxonomy import BY_NAME

EMAIL = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9-]+(?:\.[A-Z0-9-]+)*\.[A-Z]{2,}", re.I)
PHONE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)")
SSN = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)|(?<!\d)\d{9}(?!\d)")
CARD = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
KEYS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
]


def _luhn(digits: str) -> bool:
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _f(text, cat):
    return {"text": text, "category": cat, "tier": BY_NAME[cat].tier}


def predict(prompt: str) -> list[dict]:
    out, taken = [], []

    def add(m, cat):
        if any(m.start() < e and s < m.end() for s, e in taken):
            return
        taken.append((m.start(), m.end()))
        out.append(_f(m.group(0), cat))

    for m in CARD.finditer(prompt):
        if _luhn(re.sub(r"[ -]", "", m.group(0))):
            add(m, "CARD_NUMBER")
    for rx in KEYS:
        for m in rx.finditer(prompt):
            add(m, "CREDENTIAL")
    for m in SSN.finditer(prompt):
        add(m, "GOV_ID")
    for m in EMAIL.finditer(prompt):
        add(m, "EMAIL")
    for m in PHONE.finditer(prompt):
        add(m, "PHONE")
    return out
