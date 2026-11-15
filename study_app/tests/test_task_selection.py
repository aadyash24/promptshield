"""Task assignment, participant text, and log/inspector integration."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox
from study.tasks import TaskManager
from ui.study_setup_widget import StudySetupWidget
from ui.main_window import MainWindow
from services.session_logger import create_logger
from analytics.session_data import load_session
from analytics.study_analysis import load_study, summarize_study, analyze_session
from ui.session_results_widget import SessionResultsWindow
from ui.study_overview_widget import StudyOverviewWindow


class TaskSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_assignment_and_workspace(self):
        for task in TaskManager().tasks:
            for condition in ("active", "silent", "dev"):
                with self.subTest(task=task["id"], condition=condition):
                    setup = StudySetupWidget()
                    signals = []
                    setup.study_started.connect(lambda *args: signals.append(args))
                    setup.task_combo.setCurrentIndex(setup.task_combo.findData(task["id"]))
                    setup.condition_combo.setCurrentIndex(setup.condition_combo.findData(condition))
                    setup.id_input.setText("TEST")
                    setup._continue_to_consent()
                    self.assertIn(task["character"]["name"], setup.task_information.text())
                    if condition != "dev":
                        self.assertEqual(signals, [])
                        setup.consent_box.setChecked(True)
                        setup._begin()
                    self.assertEqual(signals, [("DEV" if condition == "dev" else "TEST", condition, task["id"], False)])
                    setup.close()
            workspace = MainWindow(task["id"])
            self.assertEqual(workspace.profile_window.profile_data["id"], task["id"])
            self.assertEqual(workspace.document_panel.document_type, task["document_type"])
            self.assertIn(task["recipient"], workspace.document_panel.editor.placeholderText())
            self.assertIn(task["character"]["name"].split()[0], workspace.task_panel.profile_button.text())
            if task["id"] == "work_arrangement_01":
                labels = " ".join(w.text() for w in workspace.findChildren(QLabel))
                self.assertNotIn("Maya", labels)
                self.assertNotIn("Jordan", labels)
                self.assertEqual(workspace.profile_window.tabs.tabText(0), "Schedule")
            submissions = []
            workspace.document_panel.document_submitted.connect(submissions.append)
            workspace.document_panel.set_document("Synthetic draft")
            with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
                workspace.document_panel.submit_document()
            self.assertEqual(submissions, ["Synthetic draft"])
            self.assertTrue(workspace.document_panel.editor.isReadOnly())
            workspace.chat_panel.shutdown()
            workspace.close()
        with self.assertRaises(ValueError):
            TaskManager("missing")

    def test_logs_and_inspectors_separate_tasks(self):
        with tempfile.TemporaryDirectory() as directory:
            for task in TaskManager().tasks:
                for condition in ("active", "silent", "dev"):
                    logger = create_logger("TEST", condition, task_id=task["id"],
                        task_title=task["title"], task_version=task["version"],
                        data_dir=directory, survey_enabled=True)
                    logger.log_event("task_started", task_version=task["version"])
                    logger.log_event("document_submitted", word_count=2)
                    logger.log_survey({}, status="skipped")
                    logger.close()
                    if condition != "dev":
                        session = load_session(logger.directory)
                        self.assertTrue(all(e["task_id"] == task["id"] for e in session["events"]))
                        self.assertEqual(session["metadata"]["task_version"], task["version"])
                        self.assertNotIn("Generalized anxiety disorder", logger.events_path.read_text())
            records = load_study(directory)
            self.assertEqual(len(records), 4)
            summary = summarize_study(records)
            for task in TaskManager().tasks:
                for condition in ("active", "silent"):
                    self.assertEqual(summary["by_task"][task["id"]][condition]["sessions"], 1)
            inspector = SessionResultsWindow(directory)
            self.assertEqual(inspector.session_list.count(), 4)
            inspector.task_filter.setCurrentIndex(inspector.task_filter.findData("work_arrangement_01"))
            self.assertEqual(inspector.session_list.count(), 2)
            self.assertIn("Temporary Work Arrangement", inspector.session_subtitle.text())
            inspector.refresh_sessions()
            self.assertEqual(inspector.session_list.count(), 2)
            inspector.close()
            with patch("ui.study_overview_widget.load_study", return_value=records):
                overview = StudyOverviewWindow()
                self.assertEqual(len(overview.figure.axes[0].patches), 4)
                overview.task_filter.setCurrentIndex(overview.task_filter.findData("work_arrangement_01"))
                self.assertEqual(overview.table.rowCount(), 2)
                self.assertEqual(len(overview.figure.axes[0].patches), 2)
                overview.close()

    def test_historical_task_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            logger = create_logger("OLD", "silent", data_dir=directory)
            logger.log_event("task_started", task_version="hardship_02")
            logger.close()
            result = analyze_session(load_session(logger.directory))
            self.assertEqual(result["task_title"], "Financial Hardship Request")
            self.assertEqual(result["task_version"], "hardship_02")
