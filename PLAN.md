# Project plan: Oct 16 to Nov 24

Human Factors in Cybersecurity. A local browser extension that warns people before sensitive information goes into an AI chatbot prompt, and a user study of whether it changes what they share.

Fill in names: **A** = ________  **B** = ________  **C** = ________  **D** = ________

## How the work is split

Nobody is "the model person" or "the slides person". Instead, **each person owns one slice of the problem from start to finish**, so everyone does real work on all five areas: the model, the extension, the demo, the study, and the presentation and report.

A slice is a group of data categories, plus the persona that exercises them in the study. The four slices cover all 18 categories in `finetune/taxonomy.py`.

| | Slice | Categories | Study persona and task |
| --- | --- | --- | --- |
| **A** | Financial | `FIN_INSTITUTION`, `INCOME`, `BALANCE_DEBT`, `CARD_NUMBER`, `BANK_ACCOUNT` | Maya Okafor, `bank`: dispute a double charge |
| **B** | Medical (see `finetune/MEDICAL.md`) | `MED_PROVIDER`, `MED_CONDITION`, `MEDICATION`, `MED_RECORD_ID`, `SENSITIVE_HEALTH` | Daniel Reyes, `insurer`: appeal a denied claim |
| **C** | Personal identifiers | `PERSON_NAME`, `DATE_OF_BIRTH`, `GOV_ID`, `HOME_ADDRESS` | Priya Nair, `rental`: rental application note |
| **D** | Contact, work, secrets | `EMAIL`, `PHONE`, `WORKPLACE_SCHOOL`, `CREDENTIAL` | Marcus Bell, `script`: debug a script with an API key |

Everyone gets **one job in each area**. The jobs are the same size, and each person's slice and jobs are chosen so nobody is on the same thing as someone else.

| Area | A | B | C | D |
| --- | --- | --- | --- | --- |
| **Model: training experiment** | LLM: Qwen3-1.7B with LoRA | LLM: Qwen3-0.6B with LoRA (small and faster) | Token classifier: distilbert-base-uncased | Token classifier: distilbert-base-cased |
| **Model: zero-shot base comparison** | Qwen3-0.6B | Qwen3-1.7B | Qwen3-4B | Qwen3-1.7B (zero-shot, base for the size comparison) |
| **Model: slice analysis** | Per-category results and errors for financial | Same for medical | Same for personal identifiers | Same for contact, work, secrets |
| **Extension component** | Detection pipeline: server, latency, one-command start | Warning card and highlights, tested on real chat sites | Safer rewrite and the leak check, 10 before and after examples | Study mode: mock chat, logging, log analysis |
| **Demo** | Scene 1: bank task, about 40 seconds | Scene 2: insurer task | Scene 3: rental task | Scene 4: script task |
| **Study role** | Ethics: IRB question and the final consent form | Recruiting and scheduling, participant tracker | Session script, survey, and the pilot session | Log analysis and the results tables |
| **Presentation** | Intro and problem | System and architecture | Method and study design | Limits, ethics, next steps |
| **Report section** | Introduction and background | System design | Study method | Discussion and limitations |
| **Plus, in every slice** | Your slice's results slide, your demo scene, your results paragraph, and 15 handwritten prompts for your categories | same | same | same |

**Everyone also:** recruits at least 4 study participants and runs their own sessions, and reviews one teammate's work each phase. Review pairs: **A with B**, **C with D**.

## Rules that keep it streamlined

1. **One branch per person per task**, named `a/zero-shot`, `b/card-ui`, and so on. Open a pull request into `main`. The review partner approves. Never push straight to `main`.
2. **Commit under your own name and school email.** Check `git config user.email` before the first commit.
3. **Each person works in their own files where possible.** Handwritten prompts go in `finetune/handwritten_extra/<yourname>.py`, which prevents merge conflicts. Shared files (`taxonomy.py`, `templates.py`, `content.ts`) change only through a pull request and a reviewer.
4. **Daily 10 minute check-in** in the team chat: done, doing today, blocked.
5. **Numbers come from files, not from memory.** Use `finetune/results/*/report.md` for model numbers and `finetune/study_logs/` for study numbers.
6. **Never wait on the model.** The demo always works with `python serve.py --regex-only`. The fine-tuned model is an upgrade, not a dependency.
7. **Do not tune on the test set.** Choose the best model using the `val` split. Run `test` once for the winner.
8. **Blocked for more than an hour? Say so.** Every step is a command in a README, so anyone can pick up anyone's task.

## This week: Fri Oct 16 to Tue Oct 20

The progress presentation is Oct 20 or 22 (confirm which). Plan for Tuesday and treat Thursday as the buffer. The schedule is the same for everyone. Your slice and your column in the table above say what is specific to you.

| Day | Everyone does this |
| --- | --- |
| **Fri Oct 16** | **Setup (30 minutes):** clone the repo, `npm install`, `npx wxt build`, load `.output/chrome-mv3` in Chrome (`chrome://extensions`, Developer mode, Load unpacked). In `finetune/`, run `python -m pytest tests -q`, then `python serve.py --regex-only` and open `http://127.0.0.1:8765/assign?pid=test`. Type your persona's details into the mock chat and watch what gets caught. Note what the regex layer misses.<br>**Model, Colab T4:** run your zero-shot base model on `test` and on `handwritten` (`python evaluate.py --base <model> --split test --name zs-<model>`). Save `results/`.<br>**Handwritten prompts:** write your 15 in `finetune/handwritten_extra/<yourname>.py`. Run `python handwritten.py` to check them.<br>**Study role:** start your task (A emails the instructor about IRB, B starts the participant tracker, C reads the session script and survey and edits them, D checks `analyze_logs.py` runs on the e2e test logs). |
| **Sat Oct 17** | **Model, Colab T4:** run your training experiment from the table (`python train_lora.py --base ... --out out/<yourname>`). Takes about an hour. Then run `python evaluate.py ... --split val --name <yourname>-val` and post the numbers in the team chat. **At 8 pm the team picks the winner on `val` together.** The winner's owner runs `test` and `handwritten` once and shares the model folder on the team drive.<br>**Extension component:** do your job from the table (details below). |
| **Sun Oct 18** | **Slice analysis:** run `evaluate.py` for the winning model on `test` and `handwritten` in your own Colab. Read `report.md` per-category rows and `errors.jsonl` for your slice's categories. Write down the 3 most common misses and false alarms with one example each. **Do not add training data yet.** That is next week's retrain.<br>**Demo scene:** write and rehearse your 40 second scene with the winning model: the task, what you type, what the extension catches, and one thing it misses (be honest about it).<br>**Slides and report:** draft your results slide and your report paragraph from the numbers and errors. |
| **Mon Oct 19** | **Integration, one laptop:** run `serve.py` with the winning model and do all four demo scenes back to back. Fix what breaks. **Full rehearsal twice** with timing. Record a backup video of the full run. Review your partner's slides and pull request. |
| **Tue Oct 20** | Present your parts. Start the server and open the mock chat **before** the talk. Bring the adapter folder and the backup video. |

### Training commands (Saturday)

```
A:  python train_lora.py --base Qwen/Qwen3-1.7B --out out/a
B:  python train_lora.py --base Qwen/Qwen3-0.6B --out out/b
C:  python train_token.py --base distilbert-base-uncased --out out/c
D:  python train_token.py --base distilbert-base-cased --out out/d
```
Always run `--smoke` first. Evaluate on `val`:
- A and B: `python evaluate.py --base <same base> --adapter out/<you> --split val --name <you>-val`
- C and D: `python evaluate.py --token-model out/<you> --split val --name <you>-val`

The experiment compares two families: a generative LLM (reads the prompt, writes JSON findings) and a token classifier (labels each word). The token classifiers are about 100 times faster and tiny, while the LLMs may judge gray cases better. When the team picks the winner, weigh `val` scores **and** speed: the live demo needs an answer in well under a second. Final comparison is DistilBERT (token classifier) against Qwen3 (LLM). The cased and uncased DistilBERT runs show whether capitalization helps with names, and the 0.6B and 1.7B Qwen3 runs show whether size matters. Every person reports results for their own domain from every run with `--domain`. Serve the winner with `python serve.py --token-model out/<you>` or `python serve.py --base ... --adapter out/<you>`.

### Your extension job, in detail

| Person | Do this | Done when |
| --- | --- | --- |
| **A: detection pipeline** | Measure how long a prompt takes on CPU and on GPU or Apple silicon. Tune `--max-new-tokens`. Add a start script so the whole demo starts with one command. | A teammate starts the demo from the README alone. Timing numbers are in the team chat. |
| **B: warning card and highlights** | Test on a textarea and a contenteditable box. Test on chatgpt.com, claude.ai, and gemini. Fix highlight bugs. Show the type of info and its tier (somewhat or very sensitive) in the card. | Screenshots from each site in the pull request. |
| **C: safer rewrite** | Test "Use safer version" for your slice's category examples. Check the leak check still falls back to placeholders when the model leaks. Make placeholders readable, such as `[CARD_1]`. | 10 before and after examples for the slides. |
| **D: study mode** | Walk through the mock chat as both conditions. Confirm the logs hold no prompt text. Run `python study/e2e/run.py` and `python analyze_logs.py` on the output. | The e2e test passes on your laptop. A sample results table exists. |

### What each person presents (about 10 minutes total)

1. **A:** the problem and who it affects, and what is in scope
2. **B:** how the extension works, using the architecture slide
3. **C:** how we trained and evaluated the model, and the study design
4. **All four, in turn:** your demo scene (40 seconds each) with your slice's result slide
5. **D:** limits, what is not done, ethics status, and the timeline

Be plain about the limits: synthetic training data, a small handwritten test set, and a study that has not started.

## Then: Oct 21 to Nov 24

Same rule: the same schedule for everyone, with specifics from your slice.

| Dates | Milestone | What everyone does | What is specific to you |
| --- | --- | --- | --- |
| Oct 21 to 24 | **Retrain with improved data** | Use your slice's top misses to add templates in `finetune/templates.py` for your categories. Open a pull request. | One person (rotate) merges and retrains. Everyone re-evaluates their slice on `val`, then the winner on `test` once. |
| Oct 25 to 31 | **Extension, mock chat, personas, task scripts, consent forms final** | Install the extension on a fresh laptop and follow only the README. Check your persona and task read clearly. | Finish your extension job. A: final consent form and IRB confirmation. B: participant tracker and schedule. C: final session script and survey. D: final logging and analysis. |
| Nov 1 to 6 | Recruit and pilot | Recruit 4 participants. Run one pilot session each with a friend. | Fix issues in your own area. |
| **Nov 7** | **User study** | Run sessions with 4 or more participants on your own laptop. | Copy `study_logs/` to the team drive after each session. |
| Nov 8 to 14 | **Analyze logs, finalize report** | Write your results paragraph and your report section. Review your partner's section. | D runs the analysis and produces the tables. A to D each write their report section from the table above. |
| Nov 17 to 24 | **Final presentation** | Rehearse twice. Present your parts. | Same sections as the progress presentation, updated with the study results. |

### Running the study on four laptops

- Everyone runs `serve.py` on their own laptop. The server balances active and silent within each laptop, so give each member **4 participants, or any even number**, to keep the groups balanced.
- Use participant IDs with the member letter: `A01` to `A04`, `B01` to `B04`, and so on.
- After each session, copy `finetune/study_logs/` to the team drive in a folder per member. D merges the folders before running `analyze_logs.py`.
- Keep signed consent forms in a separate folder from the logs. Never write a participant's name into the logs.

## Definition of done by milestone

- **Oct 17:** Four training runs compared on `val`. The winner scored once on `test` and `handwritten`. Result reports saved and compared with the regex baseline and the zero-shot models.
- **Oct 20:** The demo runs on a clean laptop from the README, with a regex-only fallback. Slides are done. The backup video is recorded.
- **Oct 31:** A stranger can install the extension and finish a mock chat session using only the README. The IRB question is answered. Consent forms are ready.
- **Nov 7:** At least 16 participants completed all four tasks. Logs are saved for everyone.
- **Nov 14:** The report is finished. Every number comes from `results/` or `study_logs/`.

## Risks and the fallback for each

| Risk | Fallback |
| --- | --- |
| Colab disconnects mid-training | Run with `--epochs 1` first and save the adapter. Reconnect and train again from the start if needed. |
| Colab GPU is not available | Try a different account or time of day. The 0.5B model (D's run) is the smallest option. |
| Models score within noise of each other | Pick the smallest model that is close, since it runs fastest in the demo. |
| Fine-tuned model is too slow for a live demo | Run the demo with `--regex-only` and show the model results on slides. |
| Fine-tuned model scores poorly | Report it honestly. Compare against the regex baseline, show the error analysis, and say what would improve it. |
| IRB or instructor approval takes too long | Ask now. Do not recruit until it is settled. Use the extra time to improve the model. |
| Fewer than 16 participants | Report the actual number and describe results as exploratory. |
| Someone is unavailable | Their review partner takes over their tasks for that phase. |

## Decision: two tiers instead of three (Oct 18)
Information is grouped by type (medical, finance, personal). Within each type there are two tiers:
somewhat sensitive and very sensitive. The submitted proposal describes three tiers (high, medium, low), so the
final report should state that we simplified to two. Results saved before this change in `finetune/results/`
used the old three tiers and are not comparable on the tier metrics. Retrain on merge day with the new labels.

## Decision: DistilBERT detects, Qwen3 rewrites (Oct 18)
- **Detection and categorization:** the fine-tuned DistilBERT token classifier, served by `finetune/serve.py --token-model <dir>`. The extension checks after a 60 ms pause. Regex runs instantly and DistilBERT adds context-based findings. Stale checks are cancelled so slow replies never queue up.
- **Rewriting:** Qwen3 (1.7B, 4-bit, run in the browser with WebLLM) smooths the wording of a prompt whose sensitive parts were already replaced with placeholders. The rewrite is rescanned and replaced with the plain placeholder text if anything leaks. To try the smaller model, change `MODEL_ID` in `entrypoints/offscreen/main.ts`.
- **Qwen3 as a detector:** the LoRA-tuned Qwen3-0.6B detector stays in the repo as the comparison for the report. On the handwritten medical set it was more precise than DistilBERT but about 6 times slower.
- **Merge day:** only DistilBERT needs retraining on the merged data (about one minute on Colab).

## Presentation demo (no extension needed)
Run `cd finetune && python serve.py --token-model out/<model>` and open `http://127.0.0.1:8765/demo`. The page animates a prompt through the pipeline using the real DistilBERT detector. The pill at the top says "Detector: DistilBERT, live". The practice chat for the study is at `/mock`.
