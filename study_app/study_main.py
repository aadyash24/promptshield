"""PromptShield study launcher and event logging."""

import os
import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QStackedWidget,
)
from PySide6.QtCore import QTimer

# Make the sibling ps package available when this file is run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ui.main_window import MainWindow
from ui.promptshield_setup_widget import PromptShieldSetupWidget
from ui.study_complete_widget import StudyCompleteWidget
from ui.study_survey_widget import StudySurveyWidget
from study.survey import SURVEY_VERSION
from ui.study_setup_widget import StudySetupWidget
from ui.theme import study_theme
from services.session_logger import create_logger


def main():
    app = QApplication(sys.argv)

    study_theme()

    window = QStackedWidget()
    window.setWindowTitle("PromptShield User Study")
    window.resize(1500, 850)

    installation = PromptShieldSetupWidget()
    window.addWidget(installation)
    setup = StudySetupWidget()
    window.addWidget(setup)
    completion = StudyCompleteWidget()
    completion.close_requested.connect(window.close)
    window.addWidget(completion)
    survey = StudySurveyWidget()
    window.addWidget(survey)

    session = {
        "logger": None,
        "study": None,
        "completed": False,
        "message_count": 0,
        "survey_finished": False,
    }
    ollama_model = ""

    def finish_survey(answers, status="submitted"):
        if session["survey_finished"]:
            return
        try:
            session["logger"].log_survey(answers, status=status)
        except (OSError, ValueError):
            survey.save_failed()
            return
        session["survey_finished"] = True
        survey.clear_responses()
        window.setCurrentWidget(completion)
        window.setWindowTitle("PromptShield — Study Complete")
        completion.close_button.setFocus()

    survey.submitted.connect(finish_survey)
    survey.skipped.connect(lambda: finish_survey({}, status="skipped"))

    def configure_models(study):
        chat = study.chat_panel
        chat.rewriter.model = ollama_model
        if "PROMPTSHIELD_CHAT_URL" not in os.environ and "PROMPTSHIELD_CHAT_MODEL" not in os.environ:
            chat.chat_backend.model = ollama_model

    def services_ready(model):
        nonlocal ollama_model
        if session["completed"]:
            return
        ollama_model = model
        study = session["study"]
        if study is not None:
            configure_models(study)
        window.setCurrentWidget(study or setup)

    installation.ready.connect(services_ready)

    def start_study(participant_id, condition):
        if session["study"] is not None:
            return

        logger = create_logger(
            participant_id=participant_id,
            condition=condition,
            task_id="hardship_01",
            app_version="prototype-v3",
            warning_hover_tracking=True,
            interaction_tracking=True,
            survey_enabled=True,
        )

        study = MainWindow()
        configure_models(study)

        study.participant_id = participant_id
        study.study_condition = condition
        study.logger = logger

        # Dev has active warning behavior but no logs.
        display_condition = (
            "active" if condition == "dev"
            else condition
        )

        study.chat_panel.set_study_condition(
            display_condition
        )

        session["logger"] = logger
        session["study"] = study

        # ---------------------------------------------
        # Session and task events
        # ---------------------------------------------

        if condition != "dev":
            logger.log_event(
                "consent_accepted",
                consent_version="draft_3_survey_text",
            )

        logger.log_event(
            "task_started",
            task_version="hardship_02",
            chat_model=study.chat_panel.chat_backend.model,
        )

        # ---------------------------------------------
        # Character profile
        # ---------------------------------------------

        study.task_panel.profile_requested.connect(
            lambda: logger.log_event(
                "profile_opened"
            )
        )

        # ---------------------------------------------
        # PromptShield detection
        # ---------------------------------------------

        def on_detection_completed(details):
            logger.log_event(
                "detection_completed",
                **details
            )

        study.chat_panel.detection_completed.connect(
            on_detection_completed
        )
        study.chat_panel.study_event.connect(
            lambda event_type, details: logger.log_event(event_type, **details)
        )
        study.chat_panel.message_input.warning_hover_event.connect(
            lambda event_type, details: logger.log_event(event_type, **details)
        )

        # ---------------------------------------------
        # User messages
        # ---------------------------------------------

        def on_message_sent(message, context):
            session["message_count"] += 1

            logger.log_message(
                message_id=session["message_count"],
                character_count=len(message),
                word_count=len(message.split()),
                **context,
            )
            if logger.enabled:
                study.chat_panel.check_sent_message(session["message_count"], message)

        study.chat_panel.study_message_submitted.connect(
            on_message_sent
        )
        study.chat_panel.sent_detection_completed.connect(
            lambda details: logger.log_event("message_detection_completed", **details)
        )

        # ---------------------------------------------
        # AI response clipboard actions
        # ---------------------------------------------

        def on_message_copied(text):
            logger.log_event(
                "chat_message_copied",
                character_count=len(text),
                word_count=len(text.split()),
            )

        study.chat_panel.message_copied.connect(on_message_copied)

        # ---------------------------------------------
        # Final document submission
        # ---------------------------------------------

        def on_document_submitted(document):
            session["completed"] = True

            logger.log_event(
                "document_submitted",
                character_count=len(document),
                word_count=len(document.split()),
                message_count=session["message_count"],
            )
            survey.set_condition(condition)
            logger.log_event("post_study_survey_shown", survey_version=SURVEY_VERSION)
            window.setCurrentWidget(survey)
            window.setWindowTitle("PromptShield — Post-study Survey")
            next(iter(survey.fields.values())).setFocus()

        study.document_panel.document_submitted.connect(
            on_document_submitted
        )

        # ---------------------------------------------
        # Show study window
        # ---------------------------------------------

        window.addWidget(study)
        window.setCurrentWidget(study)

        window.setWindowTitle(
            "PromptShield — Writing Exercise"
        )

    def close_session():
        logger = session["logger"]

        if logger is None:
            return

        status = (
            "completed"
            if session["completed"]
            else "interrupted"
        )

        session["study"].chat_panel.shutdown()
        if session["completed"] and not session["survey_finished"]:
            logger.log_event("post_study_survey_abandoned", survey_version=SURVEY_VERSION)
        logger.close(status=status)

    setup.study_started.connect(start_study)
    def on_service_lost():
        if not session["completed"]:
            window.setCurrentWidget(installation)

    installation.service_lost.connect(on_service_lost)
    app.aboutToQuit.connect(close_session)
    app.aboutToQuit.connect(installation.shutdown)

    window.show()
    QTimer.singleShot(0, installation.start)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
