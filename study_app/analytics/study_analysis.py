
"""Cross-session analysis for PromptShield."""

from collections import Counter, defaultdict
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
    checked_messages = [
        event["details"] for event in get_events(session, "message_detection_completed")
        if event.get("details", {}).get("status") == "ok"
    ]

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

    warning_exposures = (
        counts["warning_displayed"]
        if any(
            event.get("event_type") == "warning_displayed"
            for event in events
        )
        else None
    )

    return {
        "session_id": metadata.get("session_id"),
        "participant_id": participant_id,
        "condition": condition,
        "status": metadata.get(
            "status", "unknown"
        ),
        "task_id": metadata.get("task_id"),
        "completed": counts["document_submitted"] > 0,
        "duration_seconds": (
            round(duration_ms / 1000, 2)
            if duration_ms is not None
            else None
        ),
        "messages_sent": counts["message_sent"],
        "messages_checked": len(checked_messages),
        "sensitive_messages_sent": (
            sum(details["contains_pii"] is True for details in checked_messages)
            if checked_messages else None
        ),
        "detection_checks": len(detections),
        "positive_checks": len(positive_checks),
        "warning_exposures": warning_exposures,
        "warning_hovers": count_warning_hovers(metadata, counts),
        "rewrites_requested": (
            counts["rewrite_requested"]
            if "rewrite_requested" in counts
            else None
        ),
        "rewrites_accepted": (
            counts["rewrite_accepted"]
            if "rewrite_accepted" in counts
            else None
        ),
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
        "detection_checks": stats("detection_checks"),
        "positive_checks": stats("positive_checks"),
        "warning_exposures": stats("warning_exposures"),
        "warning_hovers": stats("warning_hovers"),
        "rewrites_accepted": stats("rewrites_accepted"),
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
        "total_sessions": len(records),
        "unique_participants": len({
            record["participant_id"]
            for record in records
            if record["participant_id"]
        }),
    }
