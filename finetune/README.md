# Fine-tuning a local sensitive-information detector

Timeline milestones this folder covers: **Oct 4** (compare candidate local LLMs, pick a base),
**Oct 10** (labeled dataset across financial, medical, personal identifiers and three risk tiers),
**Oct 17** (fine-tune, then precision and recall on a held-out test set).

The model reads a prompt and returns JSON like
`{"findings":[{"text":"512-48-9034","category":"GOV_ID","tier":3}]}`.
Code finds where each `text` sits in the prompt, so the model never has to count characters.

## Read this first: what is an assumption

1. **The three risk tiers are our proposal.** They live in `taxonomy.py`. If your project proposal
   defines them differently, edit that one file, then run `python make_dataset.py` again.
2. **The training data is synthetic**, built from templates with fake values. The test split uses
   templates the model never trains on, which is much harder than a random split, but it is still
   template language. `data/handwritten.jsonl` is the more honest test. **Each teammate should add
   10 to 15 prompts to `handwritten.py` in their own style** before the final numbers are reported.
3. Nothing here has been run on a GPU yet. See "What has been verified" at the bottom.

## Run it (Google Colab, free T4 GPU, about an hour total)

In Colab choose Runtime, then Change runtime type, then T4 GPU. Then:

```python
!git clone <your-repo-url> repo        # or upload and unzip the project
%cd repo/finetune
!pip install -q -r requirements.txt
!python -m pytest tests -q              # 17 tests should pass
```

**Step 1. Zero-shot comparison of candidate base models (Oct 4 milestone).** Same instructions, no training:

```python
for m in ["Qwen/Qwen2.5-0.5B-Instruct", "Qwen/Qwen2.5-1.5B-Instruct"]:
    !python evaluate.py --base {m} --split test
```
Add `meta-llama/Llama-3.2-1B-Instruct` if you have accepted its license on Hugging Face and logged in
(`!huggingface-cli login`). The regex baseline needs no GPU: `python evaluate.py --baseline regex --split test`.

**Step 2. Fine-tune (Oct 17 milestone).** Run `--smoke` first (about a minute), then the real run:

```python
!python train_lora.py --base Qwen/Qwen2.5-1.5B-Instruct --smoke
!python train_lora.py --base Qwen/Qwen2.5-1.5B-Instruct --out out/qwen15 --merge
```
If the GPU runs out of memory, add `--grad-ckpt` or `--batch-size 2 --grad-accum 8`.

**Step 3. Evaluate the fine-tuned model on both test sets:**

```python
!python evaluate.py --base Qwen/Qwen2.5-1.5B-Instruct --adapter out/qwen15 --split test
!python evaluate.py --base Qwen/Qwen2.5-1.5B-Instruct --adapter out/qwen15 --split handwritten
```
Each run writes `results/<name>/report.md` (a table you can paste into slides), `metrics.json`, and
`errors.jsonl` (every miss and false alarm, for error analysis). Download `out/qwen15` and `results/`
from Colab before the session ends.

## What to put on the progress slides

- Table: regex baseline vs zero-shot model vs fine-tuned model, on `test` and on `handwritten`.
- The number that matters for users: **recall on tier 3**, and the **false alarm rate on clean prompts**
  (a warning that cries wolf trains people to ignore it, which is the human factors point).
- Two or three real errors from `errors.jsonl`.
- State the limits plainly: synthetic data, small handwritten set, one base model size.

## Files

| File | Purpose |
| --- | --- |
| `taxonomy.py` | Categories, domains, tiers, annotation policy. Edit tiers here |
| `slots.py`, `templates.py` | Fake value generators and prompt templates (hand-written plus a generated bank of clean topic questions) |
| `make_dataset.py` | Writes `data/train.jsonl`, `val.jsonl`, `test.jsonl`, `stats.json` |
| `handwritten.py` | Hand-labeled realistic prompts, writes `data/handwritten.jsonl` |
| `prompt.py` | The instruction and output format. Identical for zero-shot, training, and inference |
| `train_lora.py` | LoRA fine-tuning |
| `evaluate.py`, `metrics.py` | Scoring against gold labels |
| `baseline_regex.py` | Regex baseline for comparison |

## Annotation policy (what counts as sensitive)

Flag information the writer discloses about themselves or people they know. Do not flag general
questions ("what is diabetes"), public figures, fictional characters, example formats like
`XXX-XX-XXXX`, or vague symptoms with no named condition. Mental health, HIV and STIs, substance use,
reproductive and genetic health are tier 3. Copy each finding exactly as written.

## Using the model in the extension

**Fastest path (used for the demo and the study): local server.** After training and merging:

```
python serve.py --base out/adapter/merged          # the merged model folder from train_lora.py --merge
# or without merging:  python serve.py --base Qwen/Qwen2.5-1.5B-Instruct --adapter out/adapter
```
The extension calls it at `http://127.0.0.1:8765/detect`. If the server is off, the extension falls back to
regex only. On a laptop CPU a 1.5B model takes several seconds per prompt, so use a GPU or Apple silicon if
you can, or try `Qwen/Qwen2.5-0.5B-Instruct`. The server drops any finding whose text is not in the prompt.
Run `python serve.py --regex-only` to test everything without a model.

## Older notes: in-browser options (optional)

The current extension runs models in the browser with WebLLM, which only loads models compiled with
MLC. A fine-tuned model needs one of:

1. **Local server (fastest, good for the Oct 20 to 22 demo):** serve the merged model on localhost
   and have the extension call it. Still on-device, but participants must run the server.
2. **Convert for the browser:** export to ONNX for Transformers.js, or compile with MLC. Fully in-browser
   and nothing to install, but it is real work and needs testing. Start early if you want this.

## What has been verified

- Dataset checks, scoring code, regex baseline: 17 tests pass (`python -m pytest tests -q`).
- The oracle baseline scores 1.0 and the empty baseline scores 0.0, so the scorer behaves.
- **Not verified on real hardware:** `train_lora.py` and the model branch of `evaluate.py`. Run
  `--smoke` first and report any error.
