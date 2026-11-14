# Post-study survey

The survey follows final letter submission. Participants answer as themselves about
playing Maya. All questions are optional; all-blank submissions, skipped surveys,
and closing without submission remain distinguishable. Survey drafts are not saved.

## Questions and purpose

The authoritative wording and stable IDs live in `study/survey.py` (version
`disclosure_v1`). Both conditions receive the same four common questions:

- `ai_use`: understand how participants used AI, including reasons for no use.
- `detail_selection`: understand why details seemed useful or unnecessary to send.
- `disclosure_changes`: capture reported omission, removal, generalization, or keeping details.
- `task_friction`: identify barriers that may explain fewer messages or task difficulty.

Active participants also receive:

- `feedback_effect`: whether they noticed feedback and how they responded, including no effect.
- `rewrite_effect`: why they used or avoided rewriting and whether it preserved needed information.

These are explanatory open-ended questions, not a validated psychometric scale.
Do not treat self-reports as verified disclosure counts or proof that a rewrite
removed PII. Do not interpret skipped answers as "no change" or "no difficulty."

## Where responses are saved

Each session folder under `data/sessions/` contains `events.jsonl` and
`session.json`. A `post_study_survey` event stores:

- `survey_version`, `status` (`submitted` or `skipped`), and `answered_count`;
- `responses`: question IDs, the exact question wording, and `response_text`;
- null responses for unanswered questions.

Session ID, condition, task ID, and timestamps are included in the event envelope;
participant ID is in the session metadata. Session metadata identifies the policy
as `metadata_and_post_study_survey`. Survey text is not sent to the AI service.
Development mode writes no session data. Closing the app after the letter but before
survey submission records `post_study_survey_abandoned` without draft answers.

Select a session in the Session Inspector and open the **Survey Results** tab to
read the questions and answers. It shows survey status, version, and the number
of questions answered. Refresh Sessions reloads the current participant's data.
The raw survey event remains available under Events & Charts. The analysis
record also exposes `survey_status`, `survey_version`, `survey_answered_count`,
and `survey_responses`. A save error keeps the participant on the survey with
their answers available to retry. General interaction logging still rejects raw
chat/letter text fields; survey collection uses a separate validated method.

## Relating responses to the study outcome

Compare Active and Silent using sent-message detection results. Report per-participant
flagged-message counts and the share of successfully checked messages flagged,
alongside total messages, unchecked/failed checks, and participants who did not
use chat. A participant with no checked messages has an undefined flagged share,
not a zero. Fewer flagged messages can reflect less AI use, so interpret counts
and shares together. Use survey responses to explain observed behavior.

The detector measures detector-flagged disclosure, including its medical/financial
categories; this is not an independently verified count of unnecessary PII.
Keep draft detections and repeated warning events separate from sent-message
outcomes. Task duration ends at letter submission and excludes survey time.

The participant disclosure (`draft_3_survey_text`) explicitly explains full survey
text collection and session linkage. Chat, AI reply, and final letter text are
still excluded from the research event logger. Researchers should explain their
actual storage access, retention, and withdrawal arrangements before consent.
