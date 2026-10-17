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
   15 prompts in their own file, `handwritten_extra/<name>.py` (copy `_template.py`), in their own style** before the final numbers are reported.
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
for m in ["Qwen/Qwen3-0.6B", "Qwen/Qwen3-1.7B"]:
    !python evaluate.py --base {m} --split test
```
Add `meta-llama/Llama-3.2-1B-Instruct` if you have accepted its license on Hugging Face and logged in
(`!huggingface-cli login`). The regex baseline needs no GPU: `python evaluate.py --baseline regex --split test`.

**Step 2. Fine-tune (Oct 17 milestone).** Run `--smoke` first (about a minute), then the real run:

```python
!python train_lora.py --base Qwen/Qwen3-1.7B --smoke
!python train_lora.py --base Qwen/Qwen3-1.7B --out out/qwen3-17 --merge
```
If the GPU runs out of memory, add `--grad-ckpt` or `--batch-size 2 --grad-accum 8`.

**Step 3. Evaluate the fine-tuned model on both test sets:**

```python
!python evaluate.py --base Qwen/Qwen3-1.7B --adapter out/qwen3-17 --split test
!python evaluate.py --base Qwen/Qwen3-1.7B --adapter out/qwen3-17 --split handwritten
```
Each run writes `results/<name>/report.md` (a table you can paste into slides), `metrics.json`, and
`errors.jsonl` (every miss and false alarm, for error analysis). Download `out/qwen3-17` and `results/`
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
| `handwritten.py`, `handwritten_extra/` | Hand-labeled realistic prompts: a starter set plus one file per teammate. The test set is built from all of them each run |
| `prompt.py` | The instruction and output format. Identical for zero-shot, training, and inference |
| `train_lora.py` | LoRA fine-tuning |
| `evaluate.py`, `metrics.py` | Scoring against gold labels |
| `baseline_regex.py` | Regex baseline for comparison |

## Annotation policy (what counts as sensitive)

Flag information the writer discloses about themselves or people they know. Do not flag general
questions ("what is diabetes"), public figures, fictional characters, example formats like
`XXX-XX-XXXX`, or vague symptoms with no named condition. Mental health, HIV and STIs, substance use,
reproductive and genetic health are tier 3. Copy each finding exactly as written.

## Option B: a token classifier (fast, recommended to compare)

Instead of a generative LLM, fine-tune a small BERT-style encoder that labels every word
(B-GOV_ID, I-GOV_ID, O ...). It reads the same data and is scored by the same `evaluate.py`.

```
python train_token.py --base distilbert-base-uncased --smoke                 # about a minute
python train_token.py --base distilbert-base-uncased --out out/tok           # a few minutes on a T4
python evaluate.py --token-model out/tok --split val
python serve.py --token-model out/tok                                   # the extension picks it up
```
Other bases to try: `distilbert-base-cased`, `roberta-base`, `bert-base-cased`, `microsoft/deberta-v3-small` (needs a fast tokenizer;
the script stops with a clear message if the base has none). The cased DistilBERT keeps capital letters, which may help with names, so we compare it with the uncased default. Compared with the LLM it is roughly 100 times faster and about 10 to 50 times smaller, never
returns broken JSON, and cannot invent text, because spans are rebuilt from character offsets. The trade-off is
weaker judgment on gray cases such as a general question versus a real disclosure, and prompts are read in
256-token windows (longer prompts are split with overlap). Compare it with the LLM on `val`, and run `test`
once for the winner.

Verified here without a GPU or Hugging Face access: labels convert to tokens and back without loss for two
tokenizer styles (tests), a tiny random model trains and learns something in 20 seconds, and `evaluate.py` and
`serve.py` run with it. Not verified: a real pretrained encoder, which needs Colab.

## Using the model in the extension

**Fastest path (used for the demo and the study): local server.** After training and merging:

```
python serve.py --base out/adapter/merged          # the merged model folder from train_lora.py --merge
# or without merging:  python serve.py --base Qwen/Qwen3-1.7B --adapter out/adapter
```
The extension calls it at `http://127.0.0.1:8765/detect`. If the server is off, the extension falls back to
regex only. On a laptop CPU a 1.5B model takes several seconds per prompt, so use a GPU or Apple silicon if
you can, or try `Qwen/Qwen3-0.6B`. The server drops any finding whose text is not in the prompt.
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
