"""Token classifier plumbing, tested offline with tokenizers trained on our own prompts."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from token_model import I2L, LABELS, chunk_text, decode, encode  # noqa: E402
from metrics import norm  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"


def rows(name, n=400):
    if name == "handwritten":  # built on the fly: the generated file is not committed
        from handwritten import build
        return build()[:n]
    out = []
    for line in open(DATA / f"{name}.jsonl", encoding="utf-8"):
        out.append(json.loads(line))
        if len(out) >= n:
            break
    return out


def build_tokenizer(kind):
    from tokenizers import Tokenizer, decoders, models, normalizers, pre_tokenizers, processors, trainers
    from transformers import PreTrainedTokenizerFast

    texts = [r["prompt"] for r in rows("train", 1500)]
    if kind == "wordpiece":  # BERT style
        t = Tokenizer(models.WordPiece(unk_token="[UNK]"))
        t.normalizer = normalizers.BertNormalizer(lowercase=False)
        t.pre_tokenizer = pre_tokenizers.BertPreTokenizer()
        t.train_from_iterator(texts, trainers.WordPieceTrainer(
            vocab_size=3000, special_tokens=["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"]))
        t.post_processor = processors.TemplateProcessing(
            single="[CLS] $A [SEP]", special_tokens=[("[CLS]", t.token_to_id("[CLS]")), ("[SEP]", t.token_to_id("[SEP]"))])
        return PreTrainedTokenizerFast(tokenizer_object=t, unk_token="[UNK]", pad_token="[PAD]",
                                       cls_token="[CLS]", sep_token="[SEP]")
    t = Tokenizer(models.BPE())  # RoBERTa style byte-level BPE
    t.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    t.decoder = decoders.ByteLevel()
    t.post_processor = processors.ByteLevel(trim_offsets=True)
    t.train_from_iterator(texts, trainers.BpeTrainer(
        vocab_size=3000, special_tokens=["<s>", "</s>", "<pad>"], initial_alphabet=pre_tokenizers.ByteLevel.alphabet()))
    return PreTrainedTokenizerFast(tokenizer_object=t, bos_token="<s>", eos_token="</s>", pad_token="<pad>")


def roundtrip(tok, data):
    ok = total = 0
    bad = []
    for r in data:
        enc = encode(r["prompt"], r["findings"], tok, 256)
        offsets = tok(r["prompt"], return_offsets_mapping=True, truncation=True, max_length=256)["offset_mapping"]
        got = {(norm(f["text"]), f["category"]) for f in decode(r["prompt"], offsets, [max(l, 0) for l in enc["labels"]])}
        gold = {(norm(f["text"]), f["category"]) for f in r["findings"]}
        total += len(gold)
        ok += len(gold & got)
        if gold != got:
            bad.append((r["prompt"], gold ^ got))
    return ok / max(total, 1), bad


def test_labels_cover_every_category():
    assert LABELS[0] == "O" and len(LABELS) == 37 and I2L[1] == LABELS[1]


@pytest.mark.parametrize("kind", ["wordpiece", "bytebpe"])
def test_gold_labels_round_trip_to_gold_findings(kind):
    tok = build_tokenizer(kind)
    recall, bad = roundtrip(tok, rows("test", 300) + rows("handwritten", 100))
    assert recall >= 0.97, bad[:3]


def test_encoded_labels_line_up_with_tokens():
    tok = build_tokenizer("wordpiece")
    prompt = "my ssn is 512-48-9034 ok"
    enc = encode(prompt, [{"text": "512-48-9034", "category": "GOV_ID", "start": 10, "end": 21}], tok)
    names = [I2L[l] if l >= 0 else None for l in enc["labels"]]
    assert names[0] is None and names[-1] is None  # special tokens ignored by the loss
    assert names.count("B-GOV_ID") == 1 and names.count("I-GOV_ID") >= 1


def test_chunking_keeps_all_text_and_overlaps():
    text = ("word " * 800).strip()
    parts = chunk_text(text, size=1000, overlap=100)
    assert len(parts) > 1 and parts[0][0] == 0
    assert parts[-1][0] + len(parts[-1][1]) == len(text)
    for (a, ta), (b, _) in zip(parts, parts[1:]):
        assert b < a + len(ta)  # windows overlap, so a span on a boundary is seen whole
    assert chunk_text("short") == [(0, "short")]


def test_decode_snaps_partial_words_to_whole_words():
    prompt = "my doc is Dr. Patel and my mrn is 4471823 and I avoid gluten"
    def span(text, part):
        start = prompt.index(text) + prompt[prompt.index(text):].index(part)
        return start
    def run(part_text, label):
        s = prompt.index(part_text)
        offsets = [(s, s + len(part_text))]
        return decode(prompt, offsets, [LABELS.index(label)])
    assert run("44", "B-MED_RECORD_ID")[0]["text"] == "4471823"
    assert run("luten", "B-MEDICATION")[0]["text"] == "gluten"
    assert run(". Patel", "B-MED_PROVIDER")[0]["text"] == "Dr. Patel"
