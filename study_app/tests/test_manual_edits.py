import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from study.manual_edits import ManualEditTracker
from ui.chat_widget import ChatWidget
from ui.study_setup_widget import StudySetupWidget
from services.session_logger import create_logger
from study.survey import questions_for
from analytics.session_data import load_session
from analytics.study_analysis import analyze_session


class ManualEditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        from ui.theme import study_theme
        study_theme()

    def test_removal_restoration_and_programmatic_edits(self):
        tracker = ManualEditTracker()
        tracker.observe("Alice Alice", [{"start": 0, "end": 5, "category": "PERSON_NAME", "tier": 1}])
        self.assertEqual(tracker.edit("Alice")[0]["removed"], 1)
        self.assertEqual(tracker.summary()[0]["count"], 1)
        self.assertEqual(tracker.edit("Alice Alice")[0]["restored"], 1)
        self.assertEqual(tracker.summary(), [])
        self.assertEqual(tracker.edit("Someone", "rewrite"), [])
        self.assertEqual(tracker.summary(), [])

    def test_chat_tracks_fast_manual_edit_and_send_without_rescan(self):
        for condition in ("active", "silent"):
            w = ChatWidget(study_condition=condition)
            w.set_rewrites_enabled(False)
            events, sent = [], []
            w.study_event.connect(lambda name, details: events.append((name, details)))
            w.study_message_submitted.connect(lambda text, context: sent.append(context))
            w.message_input.setPlainText("My name is Alice")
            w.detection_timer.stop()
            w.on_detection_result(w._draft_revision, {"mode": "token", "findings": [
                {"text": "Alice", "category": "PERSON_NAME", "tier": 1}]})
            w.message_input.setPlainText("My name is someone")
            w.detection_timer.stop()
            with patch.object(w.chat_backend, "request_reply"):
                w.send_message()
            self.assertEqual(sent[0]["manual_removed_values_at_send"][0]["count"], 1)
            self.assertFalse(sent[0]["draft_scan_current"])
            self.assertEqual(events[-1][0], "draft_sensitive_edit")
            self.assertNotIn("Alice", str(events))
            self.assertEqual(w._manual_tracker.summary(), [])
            self.assertTrue(w.message_input._privacy_popup.rewrite_button.isHidden())
            with patch("ui.chat_widget.SafeRewriteWorker") as worker:
                w.rewrite_safely({})
                worker.assert_not_called()
            w.shutdown()
            w.close()

    def test_toggle_survey_and_log_metadata(self):
        setup = StudySetupWidget()
        self.assertFalse(setup.rewrites_box.isChecked())
        setup.rewrites_box.setChecked(True)
        setup.condition_combo.setCurrentIndex(setup.condition_combo.findData("dev"))
        calls = []
        setup.study_started.connect(lambda *args: calls.append(args))
        setup._continue_to_consent()
        self.assertTrue(calls[0][-1])
        setup.condition_combo.setCurrentIndex(setup.condition_combo.findData("silent"))
        self.assertFalse(setup.rewrites_box.isEnabled())
        setup.close()
        self.assertNotIn("rewrite_effect", dict(questions_for("active", False)))
        self.assertIn("rewrite_effect", dict(questions_for("active", True)))
        with tempfile.TemporaryDirectory() as d:
            log = create_logger("TEST", "active", data_dir=d, rewrites_enabled=False,
                                manual_edit_tracking=True, survey_enabled=True)
            log.log_message(manual_edit_observed_scans=1, manual_removed_values_at_send=[
                {"category": "PERSON_NAME", "tier": 1, "count": 1}], draft_id=1)
            log.log_survey({key: "" for key, _ in questions_for("active", False)})
            log.close()
            session = load_session(log.directory)
            self.assertFalse(session["metadata"]["rewrites_enabled"])
            self.assertEqual(analyze_session(session)["manual_removal_messages"], 1)

    def test_rewrite_changes_are_not_manual_and_stale_scan_is_ignored(self):
        w = ChatWidget()
        events = []
        w.study_event.connect(lambda name, details: events.append((name, details)))
        w.message_input.setPlainText("Alice")
        revision = w._draft_revision
        result = {"findings": [{"text": "Alice", "category": "PERSON_NAME", "tier": 1}]}
        w.on_detection_result(revision, result)
        w.replace_draft_range(0, 5, "someone")
        self.assertEqual(w._manual_tracker.summary(), [])
        self.assertFalse(any(name == "draft_sensitive_edit" for name, _ in events))
        scans = w._manual_tracker.scans
        w.on_detection_result(revision, result)
        self.assertEqual(w._manual_tracker.scans, scans)
        w.detection_timer.stop()
        w.shutdown()
        w.close()
