# Project plan: Oct 16 to Nov 24

Human Factors in Cybersecurity. A local browser extension that warns people before sensitive information goes into an AI chatbot prompt, and a user study of whether it changes what they share.

Fill in names: **A** = ________  **B** = ________  **C** = ________  **D** = ________

## How the work is split

Four workstreams. Each person **leads one** and does **a small slice of each of the others**, so everyone touches the model, the demo, the study and the writing. Leads decide; slices are reviewed by the lead.

| | Workstream | What the lead owns | Lead |
| --- | --- | --- | --- |
| 1 | **Model** | Colab training and evaluation, error analysis, the adapter file | A |
| 2 | **Extension and demo** | Extension build, local server, mock chat page, the live demo | B |
| 3 | **Study** | IRB question, consent form, personas and tasks, session script, log analysis | C |
| 4 | **Presentation and report** | Slides, speaker notes, the final report skeleton, the backup demo video | D |

**Everyone, regardless of workstream**
- Adds 10 to 15 realistic prompts to `finetune/handwritten.py` in their own writing style.
- Recruits at least 4 study participants and runs their own sessions.
- Presents part of the progress and final presentations.
- Writes one section of the final report.
- Reviews one teammate's pull request each phase. Review pairs: **A with B**, **C with D**.

## Rules that keep it streamlined

1. **One branch per person per task**, named `a/colab-eval`, `b/demo-script`, and so on. Open a pull request into `main`. The review partner approves. Never push straight to `main`.
2. **Commit under your own name and school email.** Check with `git config user.email` before your first commit.
3. **Daily 10 minute check-in** (call or chat), three questions: done, doing today, blocked. Post it in the team chat so nobody has to attend live.
4. **One source of truth.** Numbers for slides come from `finetune/results/*/report.md`. Study logs come from `finetune/study_logs/`. Do not retype numbers by hand.
5. **Blocked for more than an hour: say so.** Anyone can pick up anyone's task, because every step is a command in a README.
6. **Do not wait on the model.** The demo must work with `python serve.py --regex-only` at all times. The fine-tuned model is an upgrade, not a dependency.

## This week: Fri Oct 16 to Tue Oct 20

Progress presentation is Oct 20 or 22 (confirm which). Plan for Tuesday; Thursday is the buffer.

| Day | A (Model lead) | B (Demo lead) | C (Study lead) | D (Presentation lead) |
| --- | --- | --- | --- | --- |
| **Fri Oct 16** | Open Colab with a T4. Run the tests, then `train_lora.py --smoke`, then start the real training (about 1 hour). Download `out/adapter`. | Build the extension (`npm install`, `npx wxt build`), load it in Chrome, run `serve.py --regex-only`, open the mock chat and confirm the card appears. Run `python study/e2e/run.py`. | Email the instructor: does UTK IRB review or an exemption apply? Review the consent draft and personas in the Study Kit. Check the three risk tiers in `finetune/taxonomy.py` against the proposal. | **Cross-training (model):** run the zero-shot comparison in Colab for both base models (Oct 4 evidence): `evaluate.py --base Qwen/Qwen2.5-0.5B-Instruct --split test`, then the 1.5B. Save the reports. Add your handwritten prompts. |
| **Sat Oct 17** | Evaluate the fine-tuned model on `test` and `handwritten`. Save the `results/` folders. If tier 3 recall is weak, start a second run with more epochs. | **Cross-training (study):** run the whole mock chat as a participant, once as active and once with `?cond=silent`. Confirm logs appear and `analyze_logs.py` runs. Add your handwritten prompts. | **Cross-training (model):** read `errors.jsonl` from the fine-tuned run. List the 5 most common misses and false alarms with one example each. Add your handwritten prompts. | Draft the slide outline (below). Pull the numbers from the three result reports into a comparison table. **Cross-training (demo):** write the 2 minute demo script. |
| **Sun Oct 18** | Merge the adapter: `train_lora.py --merge`. Hand the folder to B. Write the "model" slides content: data, method, results, limits. | Run `serve.py --base ... --adapter ...` with the trained model. Time a prompt. If it is slower than about 5 seconds, try the 0.5B model or a GPU laptop. **Cross-training (slides):** build the architecture slide from the walkthrough page. | Finish the session script and recruiting message. **Cross-training (demo):** rehearse the demo once with the script, note anything confusing. Send the IRB answer to the team. | Build the slides from the outline. Assign speaking parts. Add the error examples from C. |
| **Mon Oct 19** | **Cross-training (study):** run one full pilot session with a friend using the mock chat. Report timing and confusion. | Freeze the demo. Record the backup video of the full flow. Write the fallback steps (regex-only) on one page. | Fix any issues from A's pilot in the consent, script or tasks. Prepare the participant ID scheme (below). | Full rehearsal with timing. Fix slides. Everyone reads the speaker notes. |
| **Tue Oct 20** | Present the model section. Bring the adapter folder on a USB stick and the results files. | Present the demo. Bring the backup video. Start the server **before** the talk. | Present the study design section. | Present the intro and wrap-up. Hold the clicker and the timer. |

### Progress presentation outline (about 10 minutes)

1. The problem and who it affects (D)
2. How the extension works, with the architecture slide (B)
3. The model: data, fine-tuning, results versus the regex baseline (A)
4. Live demo (B), with the backup video ready
5. Study design: conditions, tasks, measures, and the ethics status (C)
6. Timeline and next steps, plus what is not done yet (D)

Be plain about limits: synthetic training data, a small handwritten test set, one base model, and a study that has not started.

## Then: Oct 21 to Nov 24

| Dates | Milestone | A (Model) | B (Demo) | C (Study) | D (Presentation) |
| --- | --- | --- | --- | --- | --- |
| Oct 21 to 24 | Fix issues from the presentation feedback | Retrain or tune if the feedback asks | Cross-training (study): load the extension on a fresh laptop and follow only the README | Update consent and tasks from feedback | Collect feedback notes into a list |
| Oct 25 to 31 | **Extension, mock chat, personas, task scripts, consent forms final** | Cross-training (demo): measure latency on a participant-style laptop | Final extension build, install guide, one-page troubleshooting | IRB confirmed, consent forms printed, personas final | Cross-training (study): check that every task and question reads clearly |
| Nov 1 to 6 | Recruit and schedule, pilot once more | Pilot as researcher | Be on call for tech problems | Schedule board and ID scheme | Cross-training: recruit 4 people |
| **Nov 7** | **User study: each member runs sessions with at least 4 participants** | Run own sessions | Run own sessions | Run own sessions, collect all logs | Run own sessions |
| Nov 8 to 14 | **Analyze logs, finalize report** | Detector precision and recall section | Methods and system section | Run `analyze_logs.py`, results section | Introduction, discussion, limitations, final edit |
| Nov 17 to 24 | **Final presentation** | Model results slides | Final demo | Study results slides | Lead the deck, rehearsal, timing |

### Running the study with four laptops

- Each member uses their own laptop and runs `serve.py` there. The server balances active and silent within each laptop, so give each member **exactly 4 participants (or any even number)** to keep the groups balanced.
- Use participant IDs with the member letter: `A01` to `A04`, `B01` to `B04`, and so on.
- After each session, copy `finetune/study_logs/` to the team drive in a folder per member. Merge the folders into one before running `analyze_logs.py`.
- The consent forms stay in a separate folder from the logs. Never write a participant's name into the logs.

## Definition of done by milestone

- **Oct 17:** Fine-tuned model scored on `test` and `handwritten`. Result reports saved. Compared against the regex baseline and the zero-shot models.
- **Oct 20:** Demo runs on a clean laptop with one command, and falls back to regex only. Slides finished. Backup video recorded.
- **Oct 31:** A stranger can install the extension and finish a mock chat session using only the README. IRB question answered. Consent forms ready.
- **Nov 7:** At least 16 participants completed all four tasks. Logs saved for everyone.
- **Nov 14:** Report finished. Every number comes from `results/` or `study_logs/`.

## Risks and the fallback for each

| Risk | Fallback |
| --- | --- |
| Colab disconnects mid-training | Train with `--epochs 1` first, save the adapter, then continue. Or use a smaller base model. |
| Fine-tuned model is too slow for a live demo | Run the demo with `--regex-only` and show the model results on slides. |
| Fine-tuned model scores poorly | Report it honestly. Compare to the regex baseline, show the error analysis, and say what would improve it. |
| IRB or instructor approval takes too long | Ask now. Do not recruit until it is settled. Use the extra time to improve the model. |
| Fewer than 16 participants | Report the actual number, describe results as exploratory, and use the permutation test output as given. |
| Someone is unavailable | Their review partner takes over their tasks for that phase. Every step is in a README. |
