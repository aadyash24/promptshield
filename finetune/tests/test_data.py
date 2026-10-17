"""Checks that protect the dataset from silent bugs. Run: python -m pytest tests -q (from finetune/)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from handwritten import build as build_handwritten  # noqa: E402
from slots import luhn_digit  # noqa: E402
from taxonomy import BY_NAME  # noqa: E402
from templates import ALL, GENERATED  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"


def rows(name):
    if name == "handwritten":
        return build_handwritten()
    return [json.loads(line) for line in open(DATA / f"{name}.jsonl", encoding="utf-8")]


def test_every_span_matches_its_offsets():
    for split in ("train", "val", "test", "handwritten"):
        for r in rows(split):
            for f in r["findings"]:
                assert r["prompt"][f["start"]:f["end"]] == f["text"], (r["id"], f)
                assert f["category"] in BY_NAME
                assert f["tier"] == BY_NAME[f["category"]].tier


def test_no_template_is_shared_between_train_and_test():
    train_ids = {t for r in rows("train") + rows("val") for t in r["template_ids"]}
    test_ids = {t for r in rows("test") for t in r["template_ids"]}
    assert not train_ids & test_ids, train_ids & test_ids


def test_no_identical_prompt_in_two_splits():
    seen = {}
    for split in ("train", "val", "test"):
        for r in rows(split):
            assert r["prompt"] not in seen, (r["id"], seen[r["prompt"]])
            seen[r["prompt"]] = r["id"]


def test_negatives_have_no_findings_and_sensitive_ones_do():
    for split in ("train", "val", "test"):
        for r in rows(split):
            if r["kind"] == "negative":
                assert r["findings"] == []
            else:
                assert r["findings"]


def test_every_category_appears_in_train_and_test():
    for split in ("train", "test"):
        present = {f["category"] for r in rows(split) for f in r["findings"]}
        assert set(BY_NAME) <= present, set(BY_NAME) - present


def test_generated_card_numbers_pass_luhn():
    for r in rows("train") + rows("test"):
        for f in r["findings"]:
            if f["category"] == "CARD_NUMBER":
                digits = "".join(ch for ch in f["text"] if ch.isdigit())
                assert luhn_digit(digits[:-1]) == digits[-1], f["text"]


def test_negative_text_never_contains_a_labeled_value_shape():
    """Hard negatives must not accidentally contain a real-looking SSN, email, or card."""
    import re
    bad = re.compile(r"\b\d{3}-\d{2}-\d{4}\b|[\w.]+@[\w.]+\.\w+")
    for r in rows("train") + rows("test"):
        if r["kind"] == "negative":
            assert not bad.search(r["prompt"]), r["prompt"]


def test_template_ids_are_unique():
    ids = [t[0] for t in ALL] + [t[0] for t in GENERATED]
    assert len(ids) == len(set(ids))


def test_handwritten_builds_with_all_teammate_files_and_has_clean_and_sensitive():
    built = build_handwritten()  # fails loudly if a teammate's span is not in their prompt
    assert any(not r["findings"] for r in built) and any(r["findings"] for r in built)
    assert len({r["prompt"] for r in built}) == len(built), "duplicate handwritten prompt"


def test_heldout_medical_values_do_not_leak_into_training_pools():
    import slots

    for held, train in ((slots.CONDITIONS_HELD, slots.CONDITIONS), (slots.SENSITIVE_DX_HELD, slots.SENSITIVE_DX),
                        (slots.MEDICATIONS_HELD, slots.MEDICATIONS), (slots.CLINIC_SUFFIX_HELD, slots.CLINIC_SUFFIX)):
        assert not set(map(str.lower, held)) & set(map(str.lower, train))


def test_test_split_medical_values_are_all_unseen_in_train():
    import slots

    seen = set(map(str.lower, slots.CONDITIONS + slots.SENSITIVE_DX + slots.MEDICATIONS))
    for r in rows("test"):
        for f in r["findings"]:
            if f["category"] in ("MED_CONDITION", "SENSITIVE_HEALTH", "MEDICATION"):
                assert f["text"].lower() not in seen, (r["id"], f["text"])


def test_template_ids_unique():
    from templates import ALL as T

    ids = [t[0] for t in T]
    assert len(ids) == len(set(ids))
