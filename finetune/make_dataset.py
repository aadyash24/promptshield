#!/usr/bin/env python3
"""Generate the synthetic labeled dataset (all values are fake).

    python make_dataset.py                # writes data/train.jsonl, val.jsonl, test.jsonl

Splits:
  train / val  use only templates with holdout=False (val is for checking training, but it
               shares phrasing with train, so do NOT report val numbers as the result).
  test         uses only holdout templates the model never saw. This is the honest number.
Also see data/handwritten.jsonl (made by handwritten.py) for realistic hand-labeled prompts.
"""
import argparse
import json
import random
from collections import Counter
from pathlib import Path

from slots import Filler, render
from taxonomy import BY_NAME
from templates import GENERATED, NEGATIVE, SENSITIVE


def pools(holdout: bool):
    sens = [t for t in SENSITIVE if t[3] == holdout]
    neg_hand = [t for t in NEGATIVE if t[3] == holdout]
    neg_gen = [t for t in GENERATED if t[3] == holdout]
    return sens, neg_hand, neg_gen


def make_record(rng: random.Random, filler: Filler, sens, neg_hand, neg_gen, neg_rate: float, compound_rate: float):
    """One example: a negative, a single sensitive prompt, or a compound of two."""
    neg = neg_hand + neg_gen

    def pick_neg():
        # half handwritten negatives (some contain look-alike values), half generated topic questions
        return rng.choice(neg_hand if rng.random() < 0.5 else neg_gen)

    if rng.random() < neg_rate:
        t = pick_neg()
        text, findings = render(t[2], filler)
        return text, findings, [t[0]], "negative"

    a = rng.choice(sens)
    text, findings = render(a[2], filler)
    ids, kind = [a[0]], "sensitive"
    if rng.random() < compound_rate:
        b = rng.choice(sens) if rng.random() < 0.6 else pick_neg()
        text_b, findings_b = render(b[2], filler)
        sep = rng.choice([" ", "\n\n", " Also, "])
        shift = len(text) + len(sep)
        for f in findings_b:
            f["start"] += shift
            f["end"] += shift
        text, findings = text + sep + text_b, findings + findings_b
        ids.append(b[0])
        kind = "compound"
    return text, findings, ids, kind


PREFIXES = ["Quick question: ", "Hey! ", "Please be brief. ", "Hi Claude, ", "Thanks in advance. ", "Urgent: ", "ok so "]
SUFFIXES = [" Thanks!", " Keep it short.", " Be specific.", " Please answer in bullet points."]


def maybe_wrap(rng: random.Random, text: str, findings: list[dict]):
    """Vary the framing without changing what is sensitive. Offsets shift with the prefix."""
    if rng.random() < 0.15:
        p = rng.choice(PREFIXES)
        text = p + text
        for f in findings:
            f["start"] += len(p)
            f["end"] += len(p)
    if rng.random() < 0.12:
        text = text + rng.choice(SUFFIXES)
    return text, findings


def maybe_lowercase(rng: random.Random, text: str, findings: list[dict]):
    if rng.random() < 0.06:
        text = text.lower()
        for f in findings:
            f["text"] = f["text"].lower()
    return text, findings


def build_split(name, n, seed, holdout, neg_rate, compound_rate, seen):
    rng = random.Random(seed)
    filler = Filler(seed + 1, holdout=holdout)
    sens, neg_hand, neg_gen = pools(holdout)
    rows, tries = [], 0
    while len(rows) < n and tries < n * 20:
        tries += 1
        text, findings, ids, kind = make_record(rng, filler, sens, neg_hand, neg_gen, neg_rate, compound_rate)
        text, findings = maybe_wrap(rng, text, findings)
        text, findings = maybe_lowercase(rng, text, findings)
        if text in seen:
            continue
        seen.add(text)
        findings.sort(key=lambda f: f["start"])
        rows.append({
            "id": f"{name}-{len(rows):05d}",
            "prompt": text,
            "findings": findings,
            "template_ids": ids,
            "kind": kind,
            "split": name,
        })
    return rows


def stats(rows):
    cats = Counter(f["category"] for r in rows for f in r["findings"])
    tiers = Counter(f["tier"] for r in rows for f in r["findings"])
    kinds = Counter(r["kind"] for r in rows)
    return {"records": len(rows), "kinds": dict(kinds), "findings": sum(cats.values()),
            "by_tier": {str(k): tiers[k] for k in sorted(tiers)}, "by_category": dict(sorted(cats.items()))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path(__file__).parent / "data"))
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--train", type=int, default=3200)
    ap.add_argument("--val", type=int, default=300)
    ap.add_argument("--test", type=int, default=500)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    splits = {
        "train": build_split("train", args.train, args.seed, False, 0.50, 0.15, seen),
        "val": build_split("val", args.val, args.seed + 100, False, 0.50, 0.15, seen),
        "test": build_split("test", args.test, args.seed + 200, True, 0.45, 0.15, seen),
    }
    summary = {}
    for name, rows in splits.items():
        with open(out / f"{name}.jsonl", "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        summary[name] = stats(rows)
    (out / "stats.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    for name, s in summary.items():
        print(f"{name}: {s['records']} records, {s['findings']} findings, kinds={s['kinds']}, tiers={s['by_tier']}")
    missing = [c for c in BY_NAME if c not in summary["test"]["by_category"]]
    print("categories missing from test:", missing or "none")


if __name__ == "__main__":
    main()
