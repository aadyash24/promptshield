"""Scoring. Pure Python, no model or GPU needed.

A prediction matches a gold finding when its text matches (case-insensitive, trailing
punctuation ignored) and, in strict mode, its category matches too. Matching is one to
one, so predicting the same value twice does not earn two hits.
"""
import json
import re
from collections import Counter, defaultdict

from taxonomy import BY_NAME


def norm(s: str) -> str:
    return re.sub(r"[\s.,;:!?\"')\]]+$", "", s.strip().lower())


def _prf(tp: int, fp: int, fn: int) -> dict:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f, 4), "tp": tp, "fp": fp, "fn": fn}


def _match(gold: list[dict], pred: list[dict], strict: bool):
    """Greedy one to one matching. Returns (matched pairs, unmatched gold, unmatched pred)."""
    unmatched_gold = list(gold)
    pairs, unmatched_pred = [], []
    for p in pred:
        hit = None
        for g in unmatched_gold:
            if norm(g["text"]) == norm(p["text"]) and (not strict or g["category"] == p.get("category")):
                hit = g
                break
        if hit is None:
            unmatched_pred.append(p)
        else:
            unmatched_gold.remove(hit)
            pairs.append((hit, p))
    return pairs, unmatched_gold, unmatched_pred


def score(prompts: list[str], golds: list[list[dict]], preds: list[list[dict]]) -> dict:
    assert len(prompts) == len(golds) == len(preds)
    tot = {"strict": [0, 0, 0], "text_only": [0, 0, 0]}
    cat = defaultdict(lambda: [0, 0, 0])
    tier_gold, tier_hit = Counter(), Counter()
    tier_correct = tier_total = 0
    hallucinated = n_pred = 0
    pos = neg = fp_prompts = tp_prompts = fn_prompts = 0

    for prompt, gold, pred in zip(prompts, golds, preds):
        n_pred += len(pred)
        hallucinated += sum(1 for p in pred if norm(p["text"]) not in prompt.lower())

        for mode, strict in (("strict", True), ("text_only", False)):
            pairs, ug, up = _match(gold, pred, strict)
            tot[mode][0] += len(pairs)
            tot[mode][1] += len(up)
            tot[mode][2] += len(ug)
            if strict:
                for g, _ in pairs:
                    cat[g["category"]][0] += 1
                    tier_hit[g["tier"]] += 1
                for p in up:
                    cat[p.get("category", "?")][1] += 1
                for g in ug:
                    cat[g["category"]][2] += 1
            else:
                for g, p in pairs:
                    tier_total += 1
                    tier_correct += int(g["tier"] == p.get("tier"))
        for g in gold:
            tier_gold[g["tier"]] += 1

        if gold:
            pos += 1
            tp_prompts += int(bool(pred))
            fn_prompts += int(not pred)
        else:
            neg += 1
            fp_prompts += int(bool(pred))

    prompt_level = _prf(tp_prompts, fp_prompts, fn_prompts)
    prompt_level.update({"positive_prompts": pos, "negative_prompts": neg,
                         "false_alarm_rate": round(fp_prompts / neg, 4) if neg else 0.0})
    return {
        "strict": _prf(*tot["strict"]),
        "text_only": _prf(*tot["text_only"]),
        "tier_accuracy": round(tier_correct / tier_total, 4) if tier_total else 0.0,
        "per_tier_recall": {str(t): round(tier_hit[t] / tier_gold[t], 4) if tier_gold[t] else None for t in (1, 2)},
        "per_category": {c: {**_prf(*v), "support": v[0] + v[2]} for c, v in sorted(cat.items())},
        "prompt_level": prompt_level,
        "hallucination_rate": round(hallucinated / n_pred, 4) if n_pred else 0.0,
        "n_prompts": len(prompts),
    }


def parse_findings(raw: str):
    """Parse model output. Returns (findings, valid_json). Never raises."""
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        return [], False
    try:
        data = json.loads(raw[start:end + 1])
        items = data["findings"]
        assert isinstance(items, list)
    except Exception:
        return [], False
    out = []
    for it in items:
        if isinstance(it, dict) and isinstance(it.get("text"), str) and it["text"].strip():
            cat = it.get("category")
            tier = it.get("tier")
            if cat in BY_NAME and not isinstance(tier, int):
                tier = BY_NAME[cat].tier
            out.append({"text": it["text"], "category": cat if isinstance(cat, str) else "?", "tier": tier})
    return out, True


def report_markdown(name: str, m: dict) -> str:
    s, t, pl = m["strict"], m["text_only"], m["prompt_level"]
    lines = [
        f"### {name} ({m['n_prompts']} prompts)",
        "",
        "| Metric | Precision | Recall | F1 |",
        "| --- | --- | --- | --- |",
        f"| Findings, category must match | {s['precision']:.3f} | {s['recall']:.3f} | {s['f1']:.3f} |",
        f"| Findings, text only | {t['precision']:.3f} | {t['recall']:.3f} | {t['f1']:.3f} |",
        f"| Prompt level (any sensitive info?) | {pl['precision']:.3f} | {pl['recall']:.3f} | {pl['f1']:.3f} |",
        "",
        f"False alarm rate on clean prompts: {pl['false_alarm_rate']:.3f} "
        f"({pl['negative_prompts']} clean, {pl['positive_prompts']} sensitive). "
        f"Tier accuracy on found items: {m['tier_accuracy']:.3f}. "
        f"Recall by tier (1 somewhat sensitive, 2 very sensitive): "
        + ", ".join(f"{k}={v if v is not None else 'n/a'}" for k, v in m["per_tier_recall"].items())
        + f". Hallucinated findings: {m['hallucination_rate']:.3f}.",
        "",
        "| Category | Support | Precision | Recall | F1 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for c, v in m["per_category"].items():
        lines.append(f"| {c} | {v['support']} | {v['precision']:.3f} | {v['recall']:.3f} | {v['f1']:.3f} |")
    return "\n".join(lines)
