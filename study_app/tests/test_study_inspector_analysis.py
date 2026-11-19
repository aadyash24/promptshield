import os
from pathlib import Path
import sys
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication

from analytics.session_data import load_session, apply_analysis_exclusions
from analytics.study_analysis import analyze_session, session_analysis_details
from services.session_logger import create_logger
from ui.study_overview_widget import StudyOverviewWindow
from ui.theme import study_theme


class StudyInspectorAnalysisTests(unittest.TestCase):
    def test_date_only_message_becomes_non_pii_without_changing_raw_input(self):
        original = {"metadata": {}, "events": [{
            "event_type": "message_detection_completed", "details": {
                "contains_pii": True, "detector_contains_pii": True,
                "finding_count": 3, "detector_finding_count": 3,
                "categories": ["DATE_OF_BIRTH"], "max_tier": 2,
                "findings_by_category_and_tier": [
                    {"category": "DATE_OF_BIRTH", "tier": 2, "count": 3}],
                "detector_findings_by_category_and_tier": [
                    {"category": "DATE_OF_BIRTH", "tier": 2, "count": 3}],
            }}]}
        filtered = apply_analysis_exclusions(original)["events"][0]["details"]
        self.assertFalse(filtered["contains_pii"])
        self.assertFalse(filtered["detector_contains_pii"])
        self.assertEqual(filtered["finding_count"], 0)
        self.assertEqual(filtered["max_tier"], 0)
        self.assertEqual(original["events"][0]["details"]["finding_count"], 3)

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        study_theme()

    def create_session(self, folder):
        logger = create_logger(
            "INSPECT", "active", data_dir=folder, interaction_tracking=True
        )
        logger.log_event("task_started", task_version="hardship_02")
        logger.log_event(
            "detection_completed", draft_id=1, revision=1, finding_count=2,
            categories=["PERSON_NAME", "DATE_OF_BIRTH"], mode="token",
        )
        logger.log_event(
            "warning_dismissed", draft_id=1, revision=1,
            category="PERSON_NAME", tier=1, start=0, end=5, reason="ignore",
        )
        logger.log_event(
            "warning_dismissed", draft_id=1, revision=1,
            category="DATE_OF_BIRTH", tier=2, start=6, end=10,
            reason="misdetected",
        )
        logger.log_message(
            message_id=1, draft_id=1, character_count=10, word_count=2,
            visible_warning_count=1, manual_removed_values_at_send=[],
        )
        logger.log_event(
            "message_detection_completed", message_id=1, status="ok", mode="token",
            contains_pii=True, finding_count=1, categories=["PERSON_NAME"], max_tier=1,
            findings_by_category_and_tier=[
                {"category": "PERSON_NAME", "tier": 1, "count": 1}
            ], detector_contains_pii=True, detector_finding_count=2,
            detector_findings_by_category_and_tier=[
                {"category": "PERSON_NAME", "tier": 1, "count": 1},
                {"category": "DATE_OF_BIRTH", "tier": 2, "count": 1},
            ], participant_reported_non_pii_count=1,
            participant_reported_non_pii=[
                {"category": "DATE_OF_BIRTH", "tier": 2, "count": 1}
            ], classification_source="participant_corrected",
        )
        logger.close()
        return logger.directory

    def test_links_messages_decisions_and_detection_classes(self):
        with tempfile.TemporaryDirectory() as folder:
            session = load_session(self.create_session(folder))
            details = session_analysis_details(session)
            message = details["messages"][0]
            self.assertEqual(message["outcome"], "PII sent after ignore")
            self.assertEqual(message["ignored_count"], 1)
            self.assertEqual(message["ignored_and_sent_count"], 1)
            self.assertEqual(message["misdetected_count"], 0)
            self.assertEqual(message["detector_finding_count"], 1)
            self.assertEqual(message["finding_count"], 1)
            self.assertTrue(all(action["message_id"] == 1 for action in details["warning_actions"]))
            classes = {(row["category"], row["tier"]): row for row in details["category_stats"]}
            self.assertEqual(classes[("PERSON_NAME", 1)]["ignored"], 1)
            self.assertNotIn(("DATE_OF_BIRTH", 2), classes)
            raw = load_session(session["folder"], exclude_categories=False)
            self.assertEqual(session_analysis_details(raw)["messages"][0]["detector_finding_count"], 2)
            record = analyze_session(session)
            self.assertEqual(record["messages_pii_after_ignore"], 1)
            self.assertEqual(record["warnings_ignored"], 1)

    def test_ui_populates_every_analysis_view(self):
        with tempfile.TemporaryDirectory() as folder:
            self.create_session(folder)
            window = StudyOverviewWindow(folder)
            self.addCleanup(window.close)
            self.assertEqual(window.sessions_table.rowCount(), 1)
            self.assertEqual(window.messages_table.rowCount(), 1)
            self.assertEqual(window.actions_table.rowCount(), 1)
            self.assertEqual(window.category_table.rowCount(), 1)
            self.assertGreater(window.events_table.rowCount(), 0)
            self.assertEqual(window.comparison_view.currentData(), "totals")
            self.assertEqual(len(window.figure.axes), 1)
            self.assertEqual(window.figure.axes[0].get_ylabel(), "Total count")
            window.comparison_view.setCurrentIndex(1)
            self.assertEqual(len(window.figure.axes), 2)
            self.assertEqual(window.figure.axes[1].get_ylim(), (0.0, 100.0))
            window.percentage_scale.setCurrentIndex(1)
            self.assertEqual(window.percentage_scale.currentData(), "fit")
            self.assertNotEqual(window.figure.axes[1].get_ylim(), (0.0, 100.0))
            window.tabs.setCurrentIndex(1)
            window.sort_filter.setCurrentIndex(
                window.sort_filter.findText("Warnings ignored")
            )
            window.sort_order.setCurrentIndex(1)
            ignored = [
                int(window.messages_table.item(row, 9).text())
                for row in range(window.messages_table.rowCount())
            ]
            self.assertEqual(ignored, sorted(ignored, reverse=True))
            window.tabs.setCurrentIndex(4)
            self.assertEqual(window.sort_filter.currentText(), "Event time")
            window.tabs.setCurrentIndex(5)
            self.assertFalse(window.sort_filter.isVisible())
            self.assertEqual(window.graph_selector.currentText(), "Custom chart")
            self.assertEqual(
                [bar.get_height() for bar in window.chart_figure.axes[0].patches],
                [1],
            )
            window.custom_x.setCurrentIndex(window.custom_x.findData("condition"))
            window.custom_y.setCurrentIndex(window.custom_y.findData("raw_findings"))
            self.assertEqual(
                [bar.get_height() for bar in window.chart_figure.axes[0].patches],
                [1],
            )
            totals_index = window.graph_selector.findText(
                "PII finding totals by condition"
            )
            self.assertGreaterEqual(totals_index, 0)
            window.graph_selector.setCurrentIndex(totals_index)
            self.assertEqual(
                [bar.get_height() for bar in window.chart_figure.axes[0].patches],
                [1, 1, 1, 0],
            )
            for index in range(window.graph_selector.count()):
                window.graph_selector.setCurrentIndex(index)
                self.assertEqual(len(window.chart_figure.axes), 1)

    def test_multiple_participants_filter_and_refresh(self):
        with tempfile.TemporaryDirectory() as folder:
            for participant in ("P01", "P02", "P03"):
                logger = create_logger(participant, "active", data_dir=folder)
                logger.close()
            window = StudyOverviewWindow(folder)
            self.addCleanup(window.close)
            participant_filter = window.participant_filter
            participant_filter.checkboxes["P01"].setChecked(True)
            participant_filter.checkboxes["P03"].setChecked(True)
            self.assertEqual(
                {entry["record"]["participant_id"] for entry in window.filtered_entries},
                {"P01", "P03"},
            )
            self.assertEqual(window.sessions_table.rowCount(), 2)
            window.refresh_data()
            self.assertEqual(participant_filter.selected_values(), {"P01", "P03"})
            self.assertEqual(window.sessions_table.rowCount(), 2)
            participant_filter.clear_selection()
            self.assertEqual(window.sessions_table.rowCount(), 3)
