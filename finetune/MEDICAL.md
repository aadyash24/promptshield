# Medical slice guide (slice B)

You own five categories: `MED_PROVIDER` (tier 1, low), `MED_CONDITION` and `MEDICATION` (tier 2, medium),
`MED_RECORD_ID` and `SENSITIVE_HEALTH` (tier 3, high). Edit `taxonomy.py` to change a tier,
then rerun `make_dataset.py`.

## How the team split works

One combined model detects all categories. Every person owns the data quality and the per-domain
results for their slice. We do not train separate models per domain, because one prompt often mixes
domains ("my SSN is ... and I take metformin") and a combined model handles that in one pass. You can
still report medical-only numbers from the same run with `--domain medical`.

## What you are responsible for

1. **Labeling rules.** Everything the writer shares about themselves or someone they know counts.
   General questions ("what is a normal A1C?"), public figures, and drug or disease names used as
   topics do not. When unsure, write the case down in `handwritten_extra/aadya.py` as a prompt and decide.
2. **Data.** Value pools are in `slots.py`, templates `M01` to `M26` and medical negatives in
   `templates.py`. The test split uses held-out medical names (`*_HELD` pools), so test measures
   generalization, not memorization. Add values to the training pools. Add held-out values only to `*_HELD`.
3. **Handwritten prompts.** Replace the starter prompts in `handwritten_extra/aadya.py` with 15 in your
   own voice. Then run `python handwritten.py`.
4. **Training and evaluation.** Colab T4 commands below.
5. **Error analysis.** Read `results/<name>/errors.jsonl` and write down the top 3 failure patterns.

## Commands (from `finetune/`)

```bash
python make_dataset.py                       # only if you changed pools, templates, or taxonomy
python -m pytest tests -q

# baselines, no GPU
python evaluate.py --baseline regex --split test --domain medical
python evaluate.py --baseline oracle --split test --domain medical   # must be 1.0

# zero-shot (Colab)
python evaluate.py --base Qwen/Qwen3-1.7B --split test --domain medical --name zs-b-medical

# fine-tune (Colab T4). Smoke test first.
python train_lora.py --base Qwen/Qwen3-0.6B --out out/b --smoke
python train_lora.py --base Qwen/Qwen3-0.6B --out out/b
python evaluate.py --base Qwen/Qwen3-0.6B --adapter out/b --split val --domain medical --name b-val-medical

# only after you pick the final model on val: run test once
python evaluate.py --base Qwen/Qwen3-0.6B --adapter out/b --split test --domain medical --name b-test-medical
python evaluate.py --base Qwen/Qwen3-0.6B --adapter out/b --split handwritten --domain medical --name b-hand-medical
```

The team compares two model families, so also train the token classifier (DistilBERT) on the same data
and score it the same way:

```bash
python train_token.py --base distilbert-base-uncased --smoke
python train_token.py --base distilbert-base-uncased --out out/b-tok
python evaluate.py --token-model out/b-tok --split val --domain medical --name b-tok-val-medical
# after the team picks the final model: test once
python evaluate.py --token-model out/b-tok --split test --domain medical --name b-tok-test-medical
```

## Numbers to put on the slide

Medical-only precision, recall and F1 (strict and text-only), recall by tier, per-category table
(which of the five is weakest), and false alarm rate. Compare regex baseline, zero-shot, and
fine-tuned. Regex currently scores 0.0 on all five medical categories, which is the case for fine-tuning.

## Rules

Do not tune on `test`. Report numbers from the files in `results/`. Never use real patient or personal data.
Commit on your own branch under your own name.
