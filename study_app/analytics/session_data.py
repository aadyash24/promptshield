import json
from collections import Counter
from pathlib import Path


DEFAULT_SESSIONS_DIR = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "sessions"
)


def load_session(folder):
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

    return {
        "folder": folder,
        "metadata": metadata,
        "events": events,
        "errors": errors,
    }


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
        "rewrites_accepted": counts.get(
            "rewrite_accepted", 0
        ),
        "documents_submitted": counts.get(
            "document_submitted", 0
        ),
        "category_checks": categories,
        "event_counts": counts,
    }
