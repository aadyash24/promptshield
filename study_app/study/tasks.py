
import json
from pathlib import Path


class TaskManager:
    def __init__(self, task_id=None):
        self.tasks = []
        self.current_index = 0

        self.load_tasks()
        if task_id is not None:
            self.current_index = next((i for i, task in enumerate(self.tasks) if task["id"] == task_id), -1)
            if self.current_index < 0:
                raise ValueError(f"Unknown task ID: {task_id}")

    def load_tasks(self):
        """Load study tasks from the JSON configuration."""

        config_path = (
            Path(__file__).resolve().parent.parent
            / "config"
            / "tasks.json"
        )

        with open(config_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        self.tasks = data["tasks"]

        if not self.tasks:
            raise ValueError("No study tasks were found.")

    def load_profile(self):
        path = Path(__file__).resolve().parent.parent / "config" / self.current_task["profile_file"]
        with path.open(encoding="utf-8") as file:
            return json.load(file)

    @property
    def current_task(self):
        """Return the currently active task."""
        return self.tasks[self.current_index]

    @property
    def task_count(self):
        """Return the total number of tasks."""
        return len(self.tasks)

    @property
    def task_number(self):
        """Return the current task number (1-based)."""
        return self.current_index + 1

    def has_next_task(self):
        return self.current_index < self.task_count - 1

    def next_task(self):
        """Advance to the next task if available."""

        if not self.has_next_task():
            return None

        self.current_index += 1
        return self.current_task
