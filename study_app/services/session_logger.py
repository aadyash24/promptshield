
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = 1

# Event metadata only. Never allow raw participant text.
FORBIDDEN_FIELDS = {
    "text",
    "raw_text",
    "message",
    "prompt",
    "content",
    "letter",
    "document",
    "detected_text",
    "email",
    "phone",
    "account_number",
}


def utc_now():
    return datetime.now(timezone.utc).isoformat(
        timespec="milliseconds"
    )


def validate_metadata(value):
    """Reject common raw-text fields, including nested fields."""

    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in FORBIDDEN_FIELDS:
                raise ValueError(
                    f"Raw text field cannot be logged: {key}"
                )
            validate_metadata(item)

    elif isinstance(value, (list, tuple)):
        for item in value:
            validate_metadata(item)


class NullLogger:
    """No filesystem access or persistent records."""

    enabled = False
    session_id = None

    def log_event(self, event_type, **details):
        return None

    def log_message(self, **details):
        return None

    def close(self, status="completed"):
        return None


class SessionLogger:
    """Metadata-only logging for participant sessions."""

    enabled = True

    def __init__(
        self,
        participant_id,
        condition,
        task_id="hardship_01",
        app_version="prototype",
        data_dir=None,
        warning_hover_tracking=False,
    ):
        if condition not in ("active", "silent"):
            raise ValueError(
                "Logging is only allowed for active/silent."
            )

        if not participant_id or not all(
            c.isalnum() or c in "-_"
            for c in participant_id
        ):
            raise ValueError("Invalid participant ID.")

        self.participant_id = participant_id
        self.condition = condition
        self.task_id = task_id
        self.session_id = str(uuid.uuid4())

        self.started = time.monotonic()
        self.started_utc = utc_now()
        self.sequence = 0
        self.closed = False

        root = (
            Path(data_dir)
            if data_dir is not None
            else Path(__file__).resolve().parents[1]
            / "data" / "sessions"
        )

        self.directory = root / (
            f"{participant_id}_{self.session_id[:8]}"
        )
        self.directory.mkdir(
            parents=True,
            exist_ok=False
        )

        self.events_path = self.directory / "events.jsonl"
        self.session_path = self.directory / "session.json"

        self.metadata = {
            "schema_version": SCHEMA_VERSION,
            "session_id": self.session_id,
            "participant_id": participant_id,
            "condition": condition,
            "task_id": task_id,
            "app_version": app_version,
            "started_at_utc": self.started_utc,
            "status": "in_progress",
            "logging_policy": "metadata_only",
        }
        if warning_hover_tracking:
            self.metadata["warning_hover_tracking"] = True

        self._save_metadata()
        self.log_event("session_started")

    def elapsed_ms(self):
        return round(
            (time.monotonic() - self.started) * 1000
        )

    def _save_metadata(self):
        with self.session_path.open(
            "w", encoding="utf-8"
        ) as file:
            json.dump(
                self.metadata,
                file,
                indent=2,
                ensure_ascii=False,
            )

    def log_event(self, event_type, **details):
        if self.closed:
            return None

        if not event_type or not isinstance(
            event_type, str
        ):
            raise ValueError("Invalid event type.")

        validate_metadata(details)

        self.sequence += 1

        record = {
            "schema_version": SCHEMA_VERSION,
            "event_id": self.sequence,
            "event_type": event_type,
            "session_id": self.session_id,
            "condition": self.condition,
            "task_id": self.task_id,
            "timestamp_utc": utc_now(),
            "elapsed_ms": self.elapsed_ms(),
            "details": details,
        }

        serialized = json.dumps(
            record,
            ensure_ascii=False,
            allow_nan=False,
        )

        with self.events_path.open(
            "a", encoding="utf-8"
        ) as file:
            file.write(serialized + "\n")

        return self.sequence

    def log_message(self, **details):
        return self.log_event(
            "message_sent",
            **details
        )

    def close(self, status="completed"):
        if self.closed:
            return

        if status not in {
            "completed",
            "interrupted",
            "withdrawn",
            "abandoned",
        }:
            raise ValueError("Invalid session status.")

        self.log_event(
            "session_ended",
            status=status
        )

        self.metadata.update({
            "status": status,
            "ended_at_utc": utc_now(),
            "duration_ms": self.elapsed_ms(),
        })

        self._save_metadata()
        self.closed = True


def create_logger(participant_id, condition, **kwargs):
    if condition == "dev":
        return NullLogger()

    return SessionLogger(
        participant_id,
        condition,
        **kwargs
    )
