#!/usr/bin/env python3
"""Fine-tune a small encoder (BERT style) as a token classifier for sensitive information.

    python train_token.py --base distilbert-base-uncased --out out/tok-distilbert
    python train_token.py --smoke        # 5 steps on 64 examples, proves the pipeline runs

Much faster than the LLM route: a few minutes on a free Colab T4, about 100 times faster at
inference, and small enough to run in the browser later. Bases to compare: distilbert-base-uncased (our default), distilbert-base-cased
(keeps capital letters, which may help with names), roberta-base, microsoft/deberta-v3-small.
Evaluate with: python evaluate.py --token-model out/tok-distilbert --split val
"""
import argparse
import json
import random
from pathlib import Path

import torch
from transformers import (AutoModelForTokenClassification, AutoTokenizer, DataCollatorForTokenClassification,
                          Trainer, TrainingArguments)

from token_model import I2L, L2I, LABELS, encode

HERE = Path(__file__).parent


def load_jsonl(name):
    return [json.loads(line) for line in open(HERE / "data" / f"{name}.jsonl", encoding="utf-8")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="distilbert-base-uncased")
    ap.add_argument("--out", default=str(HERE / "out" / "token"))
    ap.add_argument("--epochs", type=float, default=4.0)
    ap.add_argument("--lr", type=float, default=5e-5)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--max-len", type=int, default=256)
    ap.add_argument("--smoke", action="store_true", help="5 steps on 64 examples to check the pipeline")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    tok = AutoTokenizer.from_pretrained(args.base)
    if not getattr(tok, "is_fast", False):
        raise SystemExit("This base has no fast tokenizer, which is needed for character offsets. Pick another base.")

    train_rows, val_rows = load_jsonl("train"), load_jsonl("val")
    if args.smoke:
        train_rows, val_rows = train_rows[:64], val_rows[:32]
    train = [encode(r["prompt"], r["findings"], tok, args.max_len) for r in train_rows]
    val = [encode(r["prompt"], r["findings"], tok, args.max_len) for r in val_rows]
    print(f"{len(train)} train and {len(val)} validation examples, {len(LABELS)} labels")

    model = AutoModelForTokenClassification.from_pretrained(
        args.base, num_labels=len(LABELS), id2label=I2L, label2id=L2I, ignore_mismatched_sizes=True)

    use_cuda = torch.cuda.is_available()
    targs = TrainingArguments(
        output_dir=str(Path(args.out) / "checkpoints"),
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size * 2,
        num_train_epochs=args.epochs,
        max_steps=5 if args.smoke else -1,
        learning_rate=args.lr,
        weight_decay=0.01,
        lr_scheduler_type="linear",
        warmup_steps=max(1, int(0.06 * (len(train) // args.batch_size) * args.epochs)),
        eval_strategy="no" if args.smoke else "epoch",
        save_strategy="no" if args.smoke else "epoch",
        save_total_limit=1,
        load_best_model_at_end=not args.smoke,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        logging_steps=1 if args.smoke else 20,
        fp16=use_cuda,
        report_to="none",
        dataloader_num_workers=0,
        seed=args.seed,
    )
    trainer = Trainer(model=model, args=targs, train_dataset=train, eval_dataset=val,
                      data_collator=DataCollatorForTokenClassification(tok))
    trainer.train()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(out))
    tok.save_pretrained(out)
    print(f"saved to {out}")


if __name__ == "__main__":
    main()
