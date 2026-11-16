# Warning dismissal tracking

Each warning offers **Dismiss warning**, followed by **Keep warning** (also
Escape/close), **Incorrect detection** (the participant says the information is
not sensitive), and **Ignore anyway** (the participant recognizes it is sensitive
but is comfortable sharing it). Each dismissal choice is a single clickable card
with its explanation inside.

Confirmed decisions suppress that occurrence and category on repeated scans.
Edits elsewhere preserve the decision and remap its character offsets while its
sentence remains identical. Changes within that sentence invalidate the decision.
Sending starts a fresh draft with no decisions. Sentence boundaries use punctuation
followed by whitespace, or newlines; this is a conservative heuristic, not semantic
context detection. Changes to another sentence may affect meaning without resetting
a decision.

Mis-detection decisions exclude matching occurrences from sent-message PII counts.
Ignored findings continue to count. Other findings in the same message still count.
The sent check snapshots the decisions before clearing the draft, including for
queued checks, and accounts for trimmed leading whitespace.

The `message_detection_completed` event retains `detector_contains_pii`,
`detector_finding_count`, and `detector_findings_by_category_and_tier`. Its usual
`contains_pii`, counts and categories reflect participant corrections, with
`classification_source`, `participant_reported_non_pii_count`, and
`participant_reported_non_pii` identifying those corrections. Existing study
disclosure metrics use the corrected classification. Participant reports are not
independently verified ground truth.

The Session Inspector shows dismissal, reported non-PII, ignore and cancellation
counts. Its event table and timeline also expose `warning_dismissal_requested`,
`warning_dismissal_cancelled`, `warning_dismissed`,
`warning_dismissals_reconciled`, and `warning_redisplay_suppressed`. Events include
draft/revision identifiers and metadata only; finding text is never logged.
Older sessions without this instrumentation show N/A for dismissal metrics.
