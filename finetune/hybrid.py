"""Model plus regex, merged the way the extension merges them (lib/regex.ts mergeSpans).

The extension runs regex instantly and the fine-tuned model alongside it. When both flag
overlapping text, the one with the higher type priority wins. For the same kind of item the
model wins, because it gives the finer label. This mirrors that so the evaluation scores the
whole pipeline, not the model alone.
"""
from baseline_regex import predict as regex_predict

PRIORITY = {
    "GOV_ID": 100, "CARD_NUMBER": 90, "CREDENTIAL": 80, "EMAIL": 70, "PHONE": 60,
    "PERSON_NAME": 50, "HOME_ADDRESS": 50,
    "WORKPLACE_SCHOOL": 40, "FIN_INSTITUTION": 40, "MED_PROVIDER": 40,
}


def _pri(cat: str) -> int:
    return PRIORITY.get(cat, 10)


def _spans(prompt: str, findings: list[dict], source: str) -> list[dict]:
    out = []
    low = prompt.lower()
    for f in findings:
        text = f["text"]
        start = prompt.find(text)
        if start < 0:
            start = low.find(text.lower())
        if start < 0:
            continue
        out.append({"start": start, "end": start + len(text), "f": f, "source": source})
    return out


def _better(a: dict, b: dict) -> bool:
    ca, cb = a["f"]["category"], b["f"]["category"]
    if a["source"] == "model" and b["source"] == "regex" and ca == cb:
        return True
    if a["source"] == "regex" and b["source"] == "model" and ca == cb:
        return False
    if _pri(ca) != _pri(cb):
        return _pri(ca) > _pri(cb)
    return a["end"] - a["start"] > b["end"] - b["start"]


def merge(prompt: str, model_findings: list[dict]) -> list[dict]:
    spans = _spans(prompt, regex_predict(prompt), "regex") + _spans(prompt, model_findings, "model")
    spans.sort(key=lambda s: (s["start"], -(s["end"] - s["start"])))
    out: list[dict] = []
    for s in spans:
        if out and s["start"] < out[-1]["end"]:
            if _better(s, out[-1]):
                out[-1] = s
        else:
            out.append(s)
    return [s["f"] for s in out]
