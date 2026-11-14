"""Run: python -m unittest discover -s study_app/tests -p test_post_study_survey.py"""

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication
from services.session_logger import SessionLogger, create_logger
from study.survey import MAX_RESPONSE_CHARS, questions_for
from ui.study_survey_widget import StudySurveyWidget
from analytics.session_data import load_session
from analytics.study_analysis import analyze_session


class SurveyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_persist_and_analyze_each_condition(self):
        for condition in ("active", "silent"):
            with self.subTest(condition=condition), tempfile.TemporaryDirectory() as root:
                logger = SessionLogger("TEST", condition, data_dir=root, survey_enabled=True)
                logger.log_event("task_started")
                logger.log_event("document_submitted", word_count=20)
                logger.log_event("post_study_survey_shown")
                before = analyze_session(load_session(logger.directory))["duration_seconds"]
                answers = {key: "" for key, _ in questions_for(condition)}
                answers["detail_selection"] = 'I left out the account detail.\n“Not needed.”'
                logger.log_survey(answers)
                with self.assertRaises(ValueError):
                    logger.log_survey(answers)
                logger.close()
                result = analyze_session(load_session(logger.directory))
                self.assertEqual(result["survey_status"], "submitted")
                self.assertEqual(result["survey_answered_count"], 1)
                self.assertEqual(result["duration_seconds"], before)
                self.assertEqual(result["survey_responses"][1]["response_text"], answers["detail_selection"])
                self.assertIsNone(result["survey_responses"][0]["response_text"])

    def test_guardrails_and_skip(self):
        with tempfile.TemporaryDirectory() as root:
            logger = SessionLogger("TEST", "silent", data_dir=root, survey_enabled=True)
            for details in ({"text": "private"}, {"nested": {"response_text": "private"}}):
                with self.assertRaises(ValueError):
                    logger.log_event("message_sent", **details)
            with self.assertRaises(ValueError):
                logger.log_survey({"unexpected_id": "private"})
            with self.assertRaises(ValueError):
                logger.log_survey({"ai_use": "private"}, status="skipped")
            answers = {key: "" for key, _ in questions_for("silent")}
            answers["ai_use"] = "x" * (MAX_RESPONSE_CHARS + 1)
            with self.assertRaises(ValueError):
                logger.log_survey(answers)
            logger.log_survey({}, status="skipped")
            result = analyze_session(load_session(logger.directory))
            self.assertEqual(result["survey_status"], "skipped")
            self.assertEqual(result["survey_answered_count"], 0)
            self.assertNotIn("private", logger.events_path.read_text())
            logger.close()

    def test_collection_requires_opt_in_and_dev_does_not_write(self):
        with tempfile.TemporaryDirectory() as root:
            logger = SessionLogger("TEST", "active", data_dir=root)
            with self.assertRaises(ValueError):
                logger.log_survey({}, status="skipped")
            logger.close()
        with tempfile.TemporaryDirectory() as root:
            logger = create_logger("TEST", "dev", data_dir=root, survey_enabled=True)
            logger.log_survey({"ai_use": "not saved"})
            logger.close()
            self.assertEqual(list(Path(root).iterdir()), [])

    def test_widget_retry_and_condition_isolation(self):
        widget = StudySurveyWidget()
        widget.set_condition("active")
        self.assertIn("feedback_effect", widget.fields)
        widget.set_condition("silent")
        self.assertNotIn("feedback_effect", widget.fields)
        submissions = []
        widget.submitted.connect(submissions.append)
        widget.fields["ai_use"].setPlainText("x" * (MAX_RESPONSE_CHARS + 1))
        widget.submit_survey()
        self.assertEqual(submissions, [])
        widget.fields["ai_use"].setPlainText("Help with the payment plan")
        widget.submit_survey()
        self.assertFalse(widget.submit_button.isEnabled())
        widget.save_failed()
        self.assertTrue(widget.submit_button.isEnabled())
        self.assertEqual(widget.fields["ai_use"].toPlainText(), "Help with the payment plan")
        widget.close()


if __name__ == "__main__":
    unittest.main()
