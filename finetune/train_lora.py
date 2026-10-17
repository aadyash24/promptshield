#!/usr/bin/env python3
"""LoRA fine-tune a small instruct model to output sensitive-info findings as JSON.

    python train_lora.py --base Qwen/Qwen3-1.7B --out out/qwen3-17

Needs a GPU (a free Colab T4 works). Plain Hugging Face Trainer plus peft, no other training
library, so it is less likely to break when versions change. Loss is computed only on the
model's answer, not on the instructions.

Try --smoke first: 5 steps on 64 examples, takes about a minute, proves everything runs.
"""
import argparse
import json
import math
import random
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments

from prompt import chat_prompt, target_json

HERE = Path(__file__).parent


def load_jsonl(name: str):
    return [json.loads(line) for line in open(HERE / "data" / f"{name}.jsonl", encoding="utf-8")]


def encode(row, tok, max_len: int):
    """Tokenize one example. Labels are -100 (ignored) everywhere except the answer."""
    prompt_text = chat_prompt(tok, row["prompt"])
    prompt_ids = tok(prompt_text, add_special_tokens=False)["input_ids"]
    answer_ids = tok(target_json(row["findings"]) + tok.eos_token, add_special_tokens=False)["input_ids"]
    ids = prompt_ids + answer_ids
    if len(ids) > max_len:
        return None
    return {"input_ids": ids, "labels": [-100] * len(prompt_ids) + answer_ids}


class Collator:
    def __init__(self, pad_id: int):
        self.pad_id = pad_id

    def __call__(self, batch):
        n = max(len(b["input_ids"]) for b in batch)
        ids = torch.full((len(batch), n), self.pad_id, dtype=torch.long)
        labels = torch.full((len(batch), n), -100, dtype=torch.long)
        mask = torch.zeros((len(batch), n), dtype=torch.long)
        for i, b in enumerate(batch):
            k = len(b["input_ids"])
            ids[i, :k] = torch.tensor(b["input_ids"])
            labels[i, :k] = torch.tensor(b["labels"])
            mask[i, :k] = 1
        return {"input_ids": ids, "labels": labels, "attention_mask": mask}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="Qwen/Qwen3-1.7B")
    ap.add_argument("--out", default=str(HERE / "out" / "adapter"))
    ap.add_argument("--epochs", type=float, default=2.0)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--grad-accum", type=int, default=4)
    ap.add_argument("--max-len", type=int, default=768)
    ap.add_argument("--lora-r", type=int, default=16)
    ap.add_argument("--grad-ckpt", action="store_true", help="save memory if you run out of GPU memory")
    ap.add_argument("--merge", action="store_true", help="also save merged full weights in out/merged")
    ap.add_argument("--smoke", action="store_true", help="5 steps on 64 examples to check the pipeline")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    use_cuda = torch.cuda.is_available()
    bf16 = use_cuda and torch.cuda.is_bf16_supported()
    # T4 has no bf16: keep weights in fp32 and let fp16 autocast do the speedup.
    dtype = torch.bfloat16 if bf16 else torch.float32

    tok = AutoTokenizer.from_pretrained(args.base)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    rows = load_jsonl("train")
    if args.smoke:
        rows = rows[:64]
    data = [e for e in (encode(r, tok, args.max_len) for r in rows) if e]
    print(f"{len(data)} of {len(rows)} training examples fit in {args.max_len} tokens "
          f"(longest {max(len(d['input_ids']) for d in data)})")

    model = AutoModelForCausalLM.from_pretrained(args.base)
    model.to(dtype)
    if args.grad_ckpt:
        model.gradient_checkpointing_enable()
        model.enable_input_require_grads()
    model = get_peft_model(model, LoraConfig(
        r=args.lora_r, lora_alpha=2 * args.lora_r, lora_dropout=0.05,
        target_modules="all-linear", task_type="CAUSAL_LM"))
    model.print_trainable_parameters()

    eff_batch = args.batch_size * args.grad_accum
    total_steps = max(1, math.ceil(len(data) / eff_batch) * math.ceil(args.epochs))
    targs = TrainingArguments(
        output_dir=str(Path(args.out) / "checkpoints"),
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        num_train_epochs=args.epochs,
        max_steps=5 if args.smoke else -1,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_steps=max(1, int(0.05 * total_steps)),
        logging_steps=10 if not args.smoke else 1,
        save_strategy="epoch" if not args.smoke else "no",
        save_total_limit=1,
        bf16=bf16,
        fp16=use_cuda and not bf16,
        report_to="none",
        remove_unused_columns=False,
        dataloader_num_workers=0,
        seed=args.seed,
    )
    Trainer(model=model, args=targs, train_dataset=data, data_collator=Collator(tok.pad_token_id)).train()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(out)
    tok.save_pretrained(out)
    print(f"saved LoRA adapter to {out}")

    if args.merge and not args.smoke:
        merged = model.merge_and_unload().to(torch.float16)
        merged.save_pretrained(out / "merged")
        tok.save_pretrained(out / "merged")
        print(f"saved merged weights to {out / 'merged'}")


if __name__ == "__main__":
    main()
