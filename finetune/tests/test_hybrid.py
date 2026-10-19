import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hybrid import merge  # noqa: E402


def f(text, cat):
    return {"text": text, "category": cat, "tier": 2}


def test_regex_ssn_beats_model_calling_it_a_phone():
    prompt = "my ssn is 527-61-3849 please help"
    out = merge(prompt, [f("527-61-3849", "PHONE")])
    assert [(x["text"], x["category"]) for x in out] == [("527-61-3849", "GOV_ID")]


def test_model_findings_regex_cannot_see_are_kept():
    prompt = "my doctor Dr. Patel said I have asthma, mail me at a@b.com"
    out = merge(prompt, [f("Dr. Patel", "MED_PROVIDER"), f("asthma", "MED_CONDITION")])
    cats = sorted(x["category"] for x in out)
    assert cats == ["EMAIL", "MED_CONDITION", "MED_PROVIDER"]


def test_same_kind_prefers_the_model_label():
    prompt = "write to a@b.com"
    out = merge(prompt, [f("a@b.com", "EMAIL")])
    assert len(out) == 1 and out[0]["category"] == "EMAIL"
