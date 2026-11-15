"""Task labels for current and historical session logs."""

TITLES = {
    "hardship_01": "Financial Hardship Request",
    "hardship_letter_01": "Financial Hardship Request",
    "work_arrangement_01": "Temporary Work Arrangement Request",
}


def task_id(metadata):
    value = metadata.get("task_id") or "unknown"
    return "hardship_01" if value == "hardship_letter_01" else value


def task_title(metadata):
    return metadata.get("task_title") or TITLES.get(task_id(metadata), task_id(metadata))


def task_version(session):
    return session["metadata"].get("task_version") or next(
        (e.get("details", {}).get("task_version") for e in session["events"]
         if e.get("event_type") == "task_started"), None
    )
