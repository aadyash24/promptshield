import json
from collections import Counter
from pathlib import Path
from copy import deepcopy


EXCLUDED_CATEGORIES = frozenset({"DATE_OF_BIRTH"})


def apply_analysis_exclusions(session):
    """Return a filtered analysis copy; never modify collected evidence."""
    session = deepcopy(session)
    session["metadata"]["analysis_excluded_categories"] = sorted(EXCLUDED_CATEGORIES)
    events = []
    for event in session["events"]:
        details = event.get("details", {})
        if details.get("category") in EXCLUDED_CATEGORIES:
            continue
        for field in ("findings_by_category_and_tier",
                      "detector_findings_by_category_and_tier",
                      "participant_reported_non_pii", "manual_removed_values_at_send", "changes"):
            if field in details:
                details[field] = [row for row in details[field]
                                  if row.get("category") not in EXCLUDED_CATEGORIES]
        if "categories" in details:
            original = details["categories"]
            details["categories"] = [c for c in original if c not in EXCLUDED_CATEGORIES]
            # Draft logs have no per-category counts. Do not invent an exact
            # remaining count for mixed-category scans.
            if not details["categories"] and original:
                details["finding_count"] = 0
            elif set(original) & EXCLUDED_CATEGORIES and "findings_by_category_and_tier" not in details:
                details["finding_count_includes_excluded_categories"] = True
        for breakdown, count, flag in (
            ("findings_by_category_and_tier", "finding_count", "contains_pii"),
            ("detector_findings_by_category_and_tier", "detector_finding_count", "detector_contains_pii"),
            ("participant_reported_non_pii", "participant_reported_non_pii_count", None),
        ):
            if breakdown in details:
                details[count] = sum(int(row.get("count", 1) or 0) for row in details[breakdown])
                if flag and flag in details:
                    details[flag] = details[count] > 0
        if "max_tier" in details and "findings_by_category_and_tier" in details:
            details["max_tier"] = max((row.get("tier", 0) or 0
                                      for row in details["findings_by_category_and_tier"]), default=0)
        if "classification_source" in details:
            details["classification_source"] = ("participant_corrected" if
                details.get("participant_reported_non_pii_count") else "detector")
        if event.get("event_type") == "warning_displayed" and not details.get("finding_count"):
            continue
        if event.get("event_type") == "draft_sensitive_edit" and not details.get("changes"):
            continue
        events.append(event)
    session["events"] = events
    return session


DEFAULT_SESSIONS_DIR = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "sessions"
)


def load_session(folder, *, exclude_categories=True):
    """Read one session directory without modifying it."""

    folder = Path(folder)
    metadata_path = folder / "session.json"
    events_path = folder / "events.jsonl"

    metadata = {}
    events = []
    errors = []

    if metadata_path.exists():
        try:
            with metadata_path.open(
                "r", encoding="utf-8"
            ) as file:
                metadata = json.load(file)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"Session metadata: {exc}")

    if events_path.exists():
        try:
            with events_path.open(
                "r", encoding="utf-8"
            ) as file:
                for line_number, line in enumerate(file, 1):
                    if not line.strip():
                        continue

                    try:
                        event = json.loads(line)

                        if not isinstance(event, dict):
                            raise ValueError(
                                "Expected a JSON object"
                            )

                        event.setdefault("details", {})
                        events.append(event)

                    except (ValueError, TypeError) as exc:
                        errors.append(
                            f"Line {line_number}: {exc}"
                        )
        except OSError as exc:
            errors.append(f"Event log: {exc}")

    events.sort(
        key=lambda event: (
            event.get("elapsed_ms", 0),
            event.get("event_id", 0)
        )
    )

    session = {
        "folder": folder,
        "metadata": metadata,
        "events": events,
        "errors": errors,
    }
    return apply_analysis_exclusions(session) if exclude_categories else session


def discover_sessions(root=DEFAULT_SESSIONS_DIR):
    """Discover all available session directories."""

    root = Path(root)

    if not root.exists():
        return []

    folders = [
        path
        for path in root.iterdir()
        if path.is_dir()
        and (
            (path / "session.json").exists()
            or (path / "events.jsonl").exists()
        )
    ]

    return sorted(
        folders,
        key=lambda path: path.name,
        reverse=True
    )


def event_counts(events):
    """Count events by their type."""

    return Counter(
        event.get("event_type", "unknown")
        for event in events
    )


def available_event_types(events):
    """Find all recorded event types automatically."""

    return sorted(event_counts(events).keys())


def count_warning_hovers(metadata, counts):
    """Count completed hovers once and distinguish missing instrumentation."""
    if metadata.get("warning_hover_tracking") or "warning_hover_ended" in counts:
        return counts["warning_hover_ended"]
    return None


def filter_events(events, event_type=None, search=""):
    """Filter events by type and optional text search."""

    result = []

    for event in events:
        if (
            event_type
            and event_type != "All events"
            and event.get("event_type") != event_type
        ):
            continue

        if search:
            searchable = json.dumps(
                event,
                ensure_ascii=False,
                default=str
            ).lower()

            if search.lower() not in searchable:
                continue

        result.append(event)

    return result


def format_duration(milliseconds):
    """Convert milliseconds to a readable duration."""

    seconds = max(0, int(milliseconds / 1000))
    minutes, remaining = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    if hours:
        return f"{hours}h {minutes}m {remaining}s"

    if minutes:
        return f"{minutes}m {remaining}s"

    return f"{remaining}s"


def summarize_session(session):
    """Calculate commonly useful session statistics."""

    metadata = session["metadata"]
    events = session["events"]
    counts = event_counts(events)
    dismissal_tracking = bool(
        metadata.get("warning_dismissal_tracking_version")
        or counts["warning_dismissal_requested"] or counts["warning_dismissed"]
    )
    dismissal_reasons = Counter(
        event.get("details", {}).get("reason")
        for event in events if event.get("event_type") == "warning_dismissed"
    )

    checks = [
        event for event in events
        if event.get("event_type")
        == "detection_completed"
    ]

    positive_checks = [
        event for event in checks
        if event.get("details", {}).get(
            "finding_count", 0
        ) > 0
    ]

    categories = Counter()

    for event in positive_checks:
        details = event.get("details", {})

        for category in details.get("categories", []):
            categories[category] += 1

    # This measures logged detection checks,
    # not unique warnings or disclosures.
    if "duration_ms" in metadata:
        duration = metadata["duration_ms"]
    elif events:
        duration = max(
            event.get("elapsed_ms", 0)
            for event in events
        )
    else:
        duration = 0

    return {
        "participant_id": metadata.get(
            "participant_id", "Unknown"
        ),
        "condition": metadata.get(
            "condition", "Unknown"
        ),
        "status": metadata.get(
            "status", "Unknown"
        ),
        "duration_ms": duration,
        "duration": format_duration(duration),
        "total_events": len(events),
        "detection_checks": len(checks),
        "positive_checks": len(positive_checks),
        "messages_sent": counts.get("message_sent", 0),
        "warnings_displayed": counts.get(
            "warning_displayed", 0
        ),
        "warning_hovers": count_warning_hovers(metadata, counts),
        "warnings_dismissed": counts["warning_dismissed"] if dismissal_tracking else None,
        "warnings_misdetected": dismissal_reasons["misdetected"] if dismissal_tracking else None,
        "warnings_ignored": dismissal_reasons["ignore"] if dismissal_tracking else None,
        "dismissals_cancelled": counts["warning_dismissal_cancelled"] if dismissal_tracking else None,
        "rewrites_accepted": counts.get(
            "rewrite_accepted", 0
        ),
        "documents_submitted": counts.get(
            "document_submitted", 0
        ),
        "category_checks": categories,
        "event_counts": counts,
    }
