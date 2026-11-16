import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from ui.chat_widget import ChatWidget
from ui.warning_dialog import WarningDismissDialog
from study.warning_dismissals import remap_dismissals
from services.session_logger import create_logger
from analytics.session_data import load_session, summarize_session
from analytics.study_analysis import analyze_session


class DismissalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def widget(self, text="Alice is here. Another sentence."):
        w = ChatWidget()
        self.addCleanup(w.close)
        self.addCleanup(w.shutdown)
        w.message_input.setPlainText(text)
        w.detection_timer.stop()
        self.result = {"findings": [{"text": "Alice", "category": "PERSON_NAME", "tier": 1}]}
        w.on_detection_result(w._draft_revision, self.result)
        return w

    def choose(self, w, label):
        def click(dialog):
            next(b for b in (dialog.cancel_button, dialog.wrong_button, dialog.ignore_button) if b.text() == label).click()
        with patch.object(WarningDismissDialog, "exec", click):
            w.confirm_warning_dismissal(w.message_input.current_findings[0])

    def test_cancel_ignore_and_rescan(self):
        w = self.widget()
        self.choose(w, "Go back")
        self.assertEqual(len(w.message_input.current_findings), 1)
        self.choose(w, "Ignore warning")
        w.on_detection_result(w._draft_revision, self.result)
        self.assertEqual(w.message_input.current_findings, [])
        self.assertEqual(list(w._dismissed_findings.values()), ["ignore"])

    def test_context_preserves_moves_and_resets_changed_sentence(self):
        w = self.widget()
        self.choose(w, "Not sensitive")
        w.message_input.setPlainText("Intro. Alice is here. Different ending.")
        w.detection_timer.stop()
        w.on_detection_result(w._draft_revision, self.result)
        self.assertEqual(w.message_input.current_findings, [])
        self.assertIn((7, 12, "PERSON_NAME"), w._dismissed_findings)
        w.message_input.setPlainText("Intro. Alice is sick. Different ending.")
        w.detection_timer.stop()
        w.on_detection_result(w._draft_revision, self.result)
        self.assertEqual(len(w.message_input.current_findings), 1)
        self.assertFalse(w._dismissed_findings)

    def test_append_to_same_sentence_resets(self):
        kept, reset = remap_dismissals("Alice", "Alice is sick", {(0, 5, "PERSON_NAME"): "misdetected"})
        self.assertFalse(kept)
        self.assertEqual(len(reset), 1)

    def test_sent_correction_logged_and_analyzed(self):
        for label, expected in [("Not sensitive", False), ("Ignore warning", True)]:
            w = self.widget("  Alice  ")
            with tempfile.TemporaryDirectory() as folder:
                log = create_logger("TEST", "active", data_dir=folder, interaction_tracking=True)
                w.study_event.connect(lambda name, details: log.log_event(name, **details))
                self.choose(w, label)
                w.study_message_submitted.connect(lambda text, context: (
                    log.log_message(message_id=1, **context), w.check_sent_message(1, text)))
                w.sent_detection_completed.connect(lambda details: log.log_event("message_detection_completed", **details))
                with patch.object(w.chat_backend, "request_reply"), patch.object(w, "start_detection"):
                    w.send_message()
                w._sent_check_id = 1
                w.on_detection_result(w._draft_revision, self.result)
                log.close()
                session = load_session(log.directory)
                record = next(e["details"] for e in session["events"] if e["event_type"] == "message_detection_completed")
                self.assertEqual(record["contains_pii"], expected)
                self.assertTrue(record["detector_contains_pii"])
                self.assertEqual(analyze_session(session)["sensitive_messages_sent"], int(expected))
                self.assertEqual(summarize_session(session)["warnings_dismissed"], 1)
                self.assertNotIn("Alice", str(session["events"]))

    def test_other_finding_still_counts_as_pii(self):
        w = self.widget("Alice and Bob")
        self.choose(w, "Not sensitive")
        w._sent_check_id = 7
        w._sent_overrides[7] = ("Alice and Bob", set(w._dismissed_findings))
        records = []
        w.sent_detection_completed.connect(records.append)
        w.on_detection_result(w._draft_revision, {"findings": [*self.result["findings"],
            {"text": "Bob", "category": "PERSON_NAME", "tier": 1}]})
        self.assertTrue(records[0]["contains_pii"])
        self.assertEqual(records[0]["finding_count"], 1)
        self.assertEqual(records[0]["participant_reported_non_pii_count"], 1)

