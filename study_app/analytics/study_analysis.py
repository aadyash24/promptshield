
"""Cross-session analysis for PromptShield."""

from collections import Counter, defaultdict
from analytics.task_metadata import task_id, task_title, task_version
from statistics import mean, median

from analytics.session_data import (
    DEFAULT_SESSIONS_DIR,
    count_warning_hovers,
    discover_sessions,
    load_session,
)


def get_events(session, event_type):
    return [
        event for event in session["events"]
        if event.get("event_type") == event_type
    ]


def get_duration_ms(session):
    """Prefer actual task completion time."""

    started = get_events(session, "task_started")
    submitted = get_events(session, "document_submitted")

    if started and submitted:
        return max(
            0,
            submitted[-1].get("elapsed_ms", 0)
            - started[0].get("elapsed_ms", 0)
        )

    return None


def analyze_session(session):
    metadata = session["metadata"]
    events = session["events"]

    participant_id = metadata.get("participant_id")
    condition = metadata.get("condition")

    counts = Counter(
        event.get("event_type")
        for event in events
    )

    detections = get_events(
        session, "detection_completed"
    )
    sent_ids = {
        event.get("details", {}).get("message_id")
        for event in get_events(session, "message_sent")
    } - {None}
    results = {}
    for event in get_events(session, "message_detection_completed"):
        details = event.get("details", {})
        if details.get("message_id") in sent_ids:
            results[details["message_id"]] = details
    checked_messages = [
        details for details in results.values()
        if details.get("status") == "ok" and isinstance(details.get("contains_pii"), bool)
    ]
    sensitive_count = sum(details["contains_pii"] for details in checked_messages)
    interaction_tracking = metadata.get("interaction_tracking", False)

    positive_checks = [
        event for event in detections
        if event.get("details", {}).get(
            "finding_count", 0
        ) > 0
    ]

    categories = Counter()

    for event in positive_checks:
        for category in event.get(
            "details", {}
        ).get("categories", []):
            categories[category] += 1

    duration_ms = get_duration_ms(session)
    surveys = get_events(session, "post_study_survey")
    survey = surveys[-1].get("details", {}) if surveys else {}
    survey_status = survey.get("status") or (
        "abandoned" if counts["post_study_survey_abandoned"] else
        "pending" if counts["post_study_survey_shown"] else "not_presented"
    )

    warning_exposures = (
        counts["warning_displayed"]
        if interaction_tracking or counts["warning_displayed"]
        else None
    )

    return {
        "session_id": metadata.get("session_id"),
        "participant_id": participant_id,
        "condition": condition,
        "status": metadata.get(
            "status", "unknown"
        ),
        "rewrites_enabled": metadata.get("rewrites_enabled"),
        "manual_edit_tracking_version": metadata.get("manual_edit_tracking_version"),
        "manual_removal_messages": sum(
            bool(e.get("details", {}).get("manual_removed_values_at_send"))
            for e in get_events(session, "message_sent")
        ) if metadata.get("manual_edit_tracking_version") else None,
        "manual_edit_events": counts["draft_sensitive_edit"] if metadata.get("manual_edit_tracking_version") else None,
        "manual_removal_observed_messages": sum(
            e.get("details", {}).get("manual_edit_observed_scans", 0) > 0
            for e in get_events(session, "message_sent")
        ) if metadata.get("manual_edit_tracking_version") else None,
        "task_id": task_id(metadata),
        "task_title": task_title(metadata),
        "task_version": task_version(session),
        "survey_status": survey_status,
        "survey_version": survey.get("survey_version", metadata.get("survey_version")),
        "survey_answered_count": survey.get("answered_count"),
        "survey_responses": survey.get("responses", []),
        "completed": counts["document_submitted"] > 0,
        "duration_seconds": (
            round(duration_ms / 1000, 2)
            if duration_ms is not None
            else None
        ),
        "messages_sent": counts["message_sent"],
        "messages_checked": len(checked_messages),
        "messages_unchecked": counts["message_sent"] - len(checked_messages),
        "sent_detection_failures": sum(d.get("status") == "failed" for d in results.values()),
        "sent_detection_interruptions": sum(d.get("status") == "interrupted" for d in results.values()),
        "sensitive_messages_sent": sensitive_count if checked_messages else None,
        "sensitive_message_rate": sensitive_count / len(checked_messages) if checked_messages else None,
        "sent_categories": dict(Counter(
            category for details in checked_messages for category in details.get("categories", [])
        )),
        "detection_checks": len(detections),
        "positive_checks": len(positive_checks),
        "warning_exposures": warning_exposures,
        "warning_hovers": count_warning_hovers(metadata, counts),
        "rewrites_requested": (
            counts["rewrite_requested"]
            if interaction_tracking or counts["rewrite_requested"]
            else None
        ),
        "rewrites_accepted": (
            counts["rewrite_accepted"]
            if interaction_tracking or counts["rewrite_accepted"]
            else None
        ),
        "rewrites_failed": counts["rewrite_failed"] if interaction_tracking else None,
        "rewrite_fallbacks": counts["rewrite_fallback_applied"] if interaction_tracking else None,
        "rewrite_fallbacks_undone": counts["rewrite_fallback_undone"] if interaction_tracking else None,
        "rewrites_discarded": counts["rewrite_discarded"] if interaction_tracking else None,
        "chat_reply_failures": counts["chat_reply_failed"] if interaction_tracking else None,
        "categories": dict(categories),
        "detector_modes": sorted(
            {event.get("details", {}).get("mode", "unknown") for event in detections}
            | {details.get("mode", "unknown") for details in checked_messages}
        ),
        "file_errors": len(session["errors"]),
        # Not currently recoverable from our old logs.
        "unnecessary_disclosures": None,
        "letter_quality_score": None,
    }


def load_study(root=DEFAULT_SESSIONS_DIR):
    """Read every active/silent session in a folder."""

    records = []

    for folder in discover_sessions(root):
        session = load_session(folder)
        record = analyze_session(session)

        record["folder"] = str(folder)

        if record["condition"] in ("active", "silent"):
            records.append(record)

    return records


def summarize_condition(records):
    """Produce descriptive statistics for one condition."""

    def stats(field):
        values = [
            r[field]
            for r in records
            if r.get(field) is not None
        ]

        if not values:
            return {
                "n": 0,
                "mean": None,
                "median": None,
            }

        return {
            "n": len(values),
            "mean": round(mean(values), 3),
            "median": round(median(values), 3),
        }

    return {
        "sessions": len(records),
        "completed": sum(
            r["completed"] for r in records
        ),
        "duration_seconds": stats("duration_seconds"),
        "messages_sent": stats("messages_sent"),
        "manual_removal_messages": stats("manual_removal_messages"),
        "manual_removal_observed_messages": stats("manual_removal_observed_messages"),
        "messages_checked": stats("messages_checked"),
        "messages_unchecked": stats("messages_unchecked"),
        "sensitive_message_rate": stats("sensitive_message_rate"),
        "detection_checks": stats("detection_checks"),
        "positive_checks": stats("positive_checks"),
        "warning_exposures": stats("warning_exposures"),
        "warning_hovers": stats("warning_hovers"),
        "rewrites_accepted": stats("rewrites_accepted"),
        "rewrite_fallbacks": stats("rewrite_fallbacks"),
        "rewrite_fallbacks_undone": stats("rewrite_fallbacks_undone"),
        "unnecessary_disclosures": stats(
            "unnecessary_disclosures"
        ),
        "letter_quality_score": stats("letter_quality_score"),
    }


def summarize_study(records):
    groups = defaultdict(list)

    for record in records:
        groups[record["condition"]].append(record)

    return {
        "active": summarize_condition(groups["active"]),
        "silent": summarize_condition(groups["silent"]),
        "by_task": {
            key: {
                condition: summarize_condition([r for r in records if r.get("task_id", "unknown") == key and r["condition"] == condition])
                for condition in ("active", "silent")
            }
            for key in sorted({r.get("task_id", "unknown") for r in records})
        },
        "total_sessions": len(records),
        "unique_participants": len({
            record["participant_id"]
            for record in records
            if record["participant_id"]
        }),
    }
