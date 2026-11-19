
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


def _breakdown_counts(items):
    counts = Counter()
    for item in items or []:
        if not isinstance(item, dict):
            continue
        key = (item.get("category", "SENSITIVE"), item.get("tier", 0))
        counts[key] += int(item.get("count", 1) or 0)
    return counts


def session_analysis_details(session):
    """Link privacy-safe message, warning, and detection metadata for inspection."""
    metadata = session["metadata"]
    events = session["events"]
    messages = {}
    warning_actions = []
    category_tiers = {}

    # Learn tiers from the metadata already recorded in this session. Keeping the
    # inspector independent of the detector package lets its standalone scripts run
    # with only study_app on Python's import path.
    for event in events:
        details = event.get("details", {})
        if event.get("event_type") == "warning_dismissed":
            category_tiers[details.get("category")] = details.get("tier")
        for field in (
            "findings_by_category_and_tier",
            "detector_findings_by_category_and_tier",
            "participant_reported_non_pii",
        ):
            for item in details.get(field, []) or []:
                if isinstance(item, dict) and item.get("category"):
                    category_tiers[item["category"]] = item.get("tier")

    for event in events:
        event_type = event.get("event_type")
        details = event.get("details", {})
        if event_type == "message_sent":
            message_id = details.get("message_id")
            if message_id is not None:
                messages.setdefault(message_id, {}).update({
                    "message_id": message_id,
                    "draft_id": details.get("draft_id"),
                    "elapsed_ms": event.get("elapsed_ms", 0),
                    "character_count": details.get("character_count"),
                    "word_count": details.get("word_count"),
                    "visible_warning_count": details.get("visible_warning_count"),
                    "manual_removed_values_at_send": details.get(
                        "manual_removed_values_at_send", []
                    ),
                })
        elif event_type == "message_detection_completed":
            message_id = details.get("message_id")
            if message_id is not None:
                messages.setdefault(message_id, {"message_id": message_id}).update({
                    "detection_status": details.get("status"),
                    "detector_contains_pii": details.get(
                        "detector_contains_pii", details.get("contains_pii")
                    ),
                    "detector_finding_count": details.get(
                        "detector_finding_count", details.get("finding_count")
                    ),
                    "detector_findings": details.get(
                        "detector_findings_by_category_and_tier",
                        details.get("findings_by_category_and_tier", []),
                    ),
                    "contains_pii": details.get("contains_pii"),
                    "finding_count": details.get("finding_count"),
                    "findings": details.get("findings_by_category_and_tier", []),
                    "reported_non_pii_count": details.get(
                        "participant_reported_non_pii_count", 0
                    ),
                    "reported_non_pii": details.get(
                        "participant_reported_non_pii", []
                    ),
                    "classification_source": details.get("classification_source", "detector"),
                    "mode": details.get("mode"),
                })
        elif event_type == "warning_dismissed":
            warning_actions.append({
                "event_id": event.get("event_id"),
                "elapsed_ms": event.get("elapsed_ms", 0),
                "draft_id": details.get("draft_id"),
                "revision": details.get("revision"),
                "category": details.get("category", "SENSITIVE"),
                "tier": details.get("tier"),
                "reason": details.get("reason"),
            })

    draft_to_message = {
        item.get("draft_id"): message_id for message_id, item in messages.items()
        if item.get("draft_id") is not None
    }
    for action in warning_actions:
        action["message_id"] = draft_to_message.get(action.get("draft_id"))

    for message in messages.values():
        actions = [
            action for action in warning_actions
            if action.get("draft_id") == message.get("draft_id")
        ]
        message["ignored"] = [a for a in actions if a.get("reason") == "ignore"]
        message["misdetected"] = [a for a in actions if a.get("reason") == "misdetected"]
        message["ignored_count"] = len(message["ignored"])
        message["misdetected_count"] = len(message["misdetected"])
        message["ignored_categories"] = sorted({a["category"] for a in message["ignored"]})
        message["misdetected_categories"] = sorted({a["category"] for a in message["misdetected"]})
        retained = _breakdown_counts(message.get("findings"))
        ignored = Counter(
            (action.get("category", "SENSITIVE"), action.get("tier"))
            for action in message["ignored"]
        )
        message["ignored_and_sent_count"] = sum(
            min(count, retained.get(key, 0)) for key, count in ignored.items()
        )
        message["ignored_and_sent_categories"] = sorted({
            category for (category, tier), count in ignored.items()
            if retained.get((category, tier), 0) and count
        })
        if message.get("detection_status") != "ok":
            message["outcome"] = message.get("detection_status") or "unchecked"
        elif message.get("contains_pii") and message["ignored_and_sent_count"]:
            message["outcome"] = "PII sent after ignore"
        elif message.get("contains_pii"):
            message["outcome"] = "PII detected"
        elif message.get("detector_contains_pii") and message["misdetected_count"]:
            message["outcome"] = "Cleared as incorrect detection"
        else:
            message["outcome"] = "No PII detected"

    category_stats = defaultdict(Counter)
    for event in events:
        details = event.get("details", {})
        if event.get("event_type") == "detection_completed":
            for category in details.get("categories", []):
                category_stats[(category, category_tiers.get(category))][
                    "draft_detection_episodes"
                ] += 1
        elif event.get("event_type") == "rewrite_requested":
            category_stats[(details.get("category", "SENSITIVE"), details.get("tier"))][
                "rewrites"
            ] += 1
    for message in messages.values():
        for key, count in _breakdown_counts(message.get("detector_findings")).items():
            category_stats[key]["sent_raw_findings"] += count
        for key, count in _breakdown_counts(message.get("findings")).items():
            category_stats[key]["sent_retained_findings"] += count
    for action in warning_actions:
        field = "ignored" if action.get("reason") == "ignore" else "misdetected"
        category_stats[(action["category"], action.get("tier"))][field] += 1

    return {
        "session_id": metadata.get("session_id"),
        "participant_id": metadata.get("participant_id"),
        "condition": metadata.get("condition"),
        "task_id": task_id(metadata),
        "task_title": task_title(metadata),
        "messages": [messages[key] for key in sorted(messages)],
        "warning_actions": warning_actions,
        "category_stats": [
            {"category": category, "tier": tier, **counts}
            for (category, tier), counts in sorted(
                category_stats.items(), key=lambda item: (item[0][0], item[0][1] or 0)
            )
        ],
        "events": events,
        "errors": session.get("errors", []),
    }


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
    details_view = session_analysis_details(session)
    warning_actions = details_view["warning_actions"]
    ignored_actions = [a for a in warning_actions if a.get("reason") == "ignore"]
    misdetected_actions = [a for a in warning_actions if a.get("reason") == "misdetected"]
    pii_after_ignore = sum(
        message.get("outcome") == "PII sent after ignore"
        for message in details_view["messages"]
    )

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
        "analysis_excluded_categories": metadata.get("analysis_excluded_categories", []),
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
        "warnings_dismissed": len(warning_actions) if (
            metadata.get("warning_dismissal_tracking_version") or warning_actions
        ) else None,
        "warnings_ignored": len(ignored_actions) if (
            metadata.get("warning_dismissal_tracking_version") or warning_actions
        ) else None,
        "warnings_misdetected": len(misdetected_actions) if (
            metadata.get("warning_dismissal_tracking_version") or warning_actions
        ) else None,
        "messages_pii_after_ignore": pii_after_ignore if (
            metadata.get("warning_dismissal_tracking_version") or warning_actions
        ) else None,
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
        "warnings_dismissed": stats("warnings_dismissed"),
        "warnings_ignored": stats("warnings_ignored"),
        "warnings_misdetected": stats("warnings_misdetected"),
        "messages_pii_after_ignore": stats("messages_pii_after_ignore"),
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
