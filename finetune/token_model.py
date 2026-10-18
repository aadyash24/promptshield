"""Token classification (NER style) detector: shared code for training, evaluation and serving.

Each token gets a label such as B-GOV_ID, I-GOV_ID or O. Spans are rebuilt from the model's own
character offsets, so the model cannot invent text that is not in the prompt.
"""
from taxonomy import BY_NAME, CATEGORIES

LABELS = ["O"] + [f"{p}-{c.name}" for c in CATEGORIES for p in ("B", "I")]
L2I = {l: i for i, l in enumerate(LABELS)}
I2L = dict(enumerate(LABELS))


def _first_content_char(prompt: str, s: int, e: int):
    """Index of the first non-space character inside [s, e), or None."""
    for k in range(s, e):
        if not prompt[k].isspace():
            return k
    return None


def encode(prompt: str, findings: list[dict], tok, max_len: int = 256):
    """Tokenize and label one example. Special tokens get -100 so the loss ignores them."""
    enc = tok(prompt, return_offsets_mapping=True, truncation=True, max_length=max_len)
    owner = {}
    for fi, f in enumerate(findings):
        for k in range(f["start"], f["end"]):
            owner[k] = fi
    labels, prev = [], None
    for s, e in enc["offset_mapping"]:
        if s == e:  # special token
            labels.append(-100)
            continue
        c = _first_content_char(prompt, s, e)
        fi = owner.get(c) if c is not None else None
        if fi is None:
            labels.append(L2I["O"])
            prev = None
        else:
            cat = findings[fi]["category"]
            labels.append(L2I[f"{'I' if prev == fi else 'B'}-{cat}"])
            prev = fi
    return {"input_ids": enc["input_ids"], "attention_mask": enc["attention_mask"], "labels": labels}


def _snap(prompt: str, s: int, e: int):
    """Grow a span to whole words. Subword tokens can leave 'luten' for 'gluten' or '44' for '4471823'.
    A span that starts at the period of 'Dr.' also takes the title in front of it."""
    while s > 0 and prompt[s].isalnum() and prompt[s - 1].isalnum():
        s -= 1
    if prompt[s] == "." and s > 0 and prompt[s - 1].isalnum():
        while s > 0 and prompt[s - 1].isalnum():
            s -= 1
    while e < len(prompt) and prompt[e].isalnum() and prompt[e - 1].isalnum():
        e += 1
    return s, e


def decode(prompt: str, offsets, label_ids) -> list[dict]:
    """Turn per-token labels back into findings with exact text from the prompt."""
    spans, cur = [], None  # cur = [category, start, end]
    for (s, e), lid in zip(offsets, label_ids):
        if s == e:
            continue
        c = _first_content_char(prompt, s, e)
        label = I2L.get(int(lid), "O")
        if c is None or label == "O":
            if cur:
                spans.append(cur)
                cur = None
            continue
        kind, cat = label.split("-", 1)
        if kind == "I" and cur and cur[0] == cat:
            cur[2] = e
        else:
            if cur:
                spans.append(cur)
            cur = [cat, c, e]
    if cur:
        spans.append(cur)
    out = []
    for cat, s, e in spans:
        s, e = _snap(prompt, s, e)
        text = prompt[s:e].rstrip()
        if text:
            out.append({"text": text, "category": cat, "tier": BY_NAME[cat].tier, "start": s, "end": s + len(text)})
    return out


def chunk_text(text: str, size: int = 1200, overlap: int = 150):
    """Split a long prompt into windows at whitespace so nothing is cut off at the model's limit."""
    if len(text) <= size:
        return [(0, text)]
    parts, start = [], 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            cut = text.rfind(" ", start + size // 2, end)
            end = cut if cut > start else end
        parts.append((start, text[start:end]))
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return parts


class TokenDetector:
    """Loads a trained token classifier and predicts findings for prompts."""

    def __init__(self, path: str, device: str | None = None, max_len: int = 256):
        import torch
        from transformers import AutoModelForTokenClassification, AutoTokenizer

        self.torch = torch
        self.device = device or ("cuda" if torch.cuda.is_available() else (
            "mps" if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available() else "cpu"))
        self.tok = AutoTokenizer.from_pretrained(path)
        self.model = AutoModelForTokenClassification.from_pretrained(path).to(self.device).eval()
        self.max_len = max_len

    def _predict_chunks(self, chunks: list[str], batch_size: int):
        results = []
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            enc = self.tok(batch, return_offsets_mapping=True, truncation=True, max_length=self.max_len,
                           padding=True, return_tensors="pt")
            offsets = enc.pop("offset_mapping")
            with self.torch.no_grad():
                logits = self.model(**{k: v.to(self.device) for k, v in enc.items()}).logits
            ids = logits.argmax(-1).cpu().tolist()
            for j, text in enumerate(batch):
                n = int(enc["attention_mask"][j].sum())
                results.append(decode(text, offsets[j][:n].tolist(), ids[j][:n]))
        return results

    def predict(self, prompts: list[str], batch_size: int = 32) -> list[list[dict]]:
        flat, owner = [], []
        for pi, p in enumerate(prompts):
            for off, part in chunk_text(p):
                flat.append(part)
                owner.append((pi, off))
        per = self._predict_chunks(flat, batch_size)
        out = [[] for _ in prompts]
        seen = [set() for _ in prompts]
        for (pi, off), found in zip(owner, per):
            for f in found:
                key = (f["start"] + off, f["text"], f["category"])
                if key not in seen[pi]:
                    seen[pi].add(key)
                    out[pi].append({"text": f["text"], "category": f["category"], "tier": f["tier"]})
        return out
