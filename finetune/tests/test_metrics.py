import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from baseline_regex import predict  # noqa: E402
from metrics import norm, parse_findings, score  # noqa: E402


def f(text, cat="EMAIL", tier=2):
    return {"text": text, "category": cat, "tier": tier}


def test_perfect_and_empty():
    gold = [[f("a@b.com")], []]
    prompts = ["mail a@b.com", "hello"]
    perfect = score(prompts, gold, [[f("a@b.com")], []])
    assert perfect["strict"]["f1"] == 1.0 and perfect["prompt_level"]["false_alarm_rate"] == 0.0
    empty = score(prompts, gold, [[], []])
    assert empty["strict"]["recall"] == 0.0 and empty["strict"]["precision"] == 0.0


def test_wrong_category_counts_only_in_text_only_mode():
    s = score(["mail a@b.com"], [[f("a@b.com", "EMAIL")]], [[f("a@b.com", "PHONE")]])
    assert s["strict"]["tp"] == 0 and s["text_only"]["tp"] == 1


def test_false_alarm_and_hallucination_are_counted():
    s = score(["hello there"], [[]], [[f("zzz@q.com")]])
    assert s["prompt_level"]["false_alarm_rate"] == 1.0
    assert s["hallucination_rate"] == 1.0


def test_duplicate_predictions_do_not_earn_two_hits():
    s = score(["mail a@b.com"], [[f("a@b.com")]], [[f("a@b.com"), f("a@b.com")]])
    assert s["strict"]["tp"] == 1 and s["strict"]["fp"] == 1


def test_text_normalization_ignores_case_and_trailing_punctuation():
    assert norm(" Hello World. ") == "hello world"
    s = score(["Email A@B.com."], [[f("A@B.com")]], [[f("a@b.com.")]])
    assert s["strict"]["tp"] == 1


def test_tier_accuracy_and_per_tier_recall():
    gold = [[f("a@b.com", "EMAIL", 2), f("123-45-6789", "GOV_ID", 3)]]
    pred = [[f("a@b.com", "EMAIL", 2), f("123-45-6789", "GOV_ID", 1)]]
    s = score(["a@b.com 123-45-6789"], gold, pred)
    assert s["tier_accuracy"] == 0.5
    assert s["per_tier_recall"]["2"] == 1.0 and s["per_tier_recall"]["3"] == 1.0


def test_parse_findings_handles_messy_output():
    good = 'Sure! {"findings":[{"text":"a@b.com","category":"EMAIL","tier":2}]} hope that helps'
    items, ok = parse_findings(good)
    assert ok and items[0]["text"] == "a@b.com"
    assert parse_findings("no json here") == ([], False)
    assert parse_findings('{"findings": "oops"}') == ([], False)
    items, ok = parse_findings('{"findings":[{"text":"x","category":"EMAIL"}]}')
    assert ok and items[0]["tier"] == 2  # missing tier is filled from the taxonomy


def test_regex_baseline_finds_structured_values_only():
    got = {(p["text"], p["category"]) for p in predict("mail jane@x.org, ssn 123-45-6789, I have asthma")}
    assert ("jane@x.org", "EMAIL") in got and ("123-45-6789", "GOV_ID") in got
    assert not any(c == "MED_CONDITION" for _, c in got)
