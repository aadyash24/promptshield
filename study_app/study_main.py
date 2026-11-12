"""PromptShield study launcher and event logging."""

import sys

from PySide6.QtWidgets import (
    QApplication,
    QStackedWidget,
)
from PySide6.QtCore import Qt

from ui.main_window import MainWindow
from ui.study_setup_widget import StudySetupWidget
from services.session_logger import create_logger


def main():
    app = QApplication(sys.argv)

    app.styleHints().setColorScheme(
        Qt.ColorScheme.Light
    )

    window = QStackedWidget()
    window.setWindowTitle("PromptShield User Study")
    window.resize(1500, 850)

    setup = StudySetupWidget()
    window.addWidget(setup)

    session = {
        "logger": None,
        "study": None,
        "completed": False,
        "message_count": 0,
    }

    def start_study(participant_id, condition):
        if session["study"] is not None:
            return

        logger = create_logger(
            participant_id=participant_id,
            condition=condition,
            task_id="hardship_01",
            app_version="prototype-v1",
            warning_hover_tracking=True,
        )

        study = MainWindow()

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
                consent_version="draft_1",
            )

        logger.log_event(
            "task_started",
            task_version="hardship_01",
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
        study.chat_panel.message_input.warning_hover_event.connect(
            lambda event_type, details: logger.log_event(event_type, **details)
        )

        # ---------------------------------------------
        # User messages
        # ---------------------------------------------

        def on_message_sent(message):
            session["message_count"] += 1

            logger.log_message(
                message_id=session["message_count"],
                character_count=len(message),
                word_count=len(message.split()),
            )
            if logger.enabled:
                study.chat_panel.check_sent_message(session["message_count"], message)

        study.chat_panel.message_submitted.connect(
            on_message_sent
        )
        study.chat_panel.sent_detection_completed.connect(
            lambda details: logger.log_event("message_detection_completed", **details)
        )

        # ---------------------------------------------
        # AI response → document interactions
        # ---------------------------------------------

        def on_insert_requested(text):
            logger.log_event(
                "document_insert_requested",
                character_count=len(text),
                word_count=len(text.split()),
            )

        study.chat_panel.insert_requested.connect(
            on_insert_requested
        )

        def on_replace_requested(text):
            logger.log_event(
                "document_replace_requested",
                character_count=len(text),
                word_count=len(text.split()),
            )

        study.chat_panel.replace_requested.connect(
            on_replace_requested
        )

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
        logger.close(status=status)

    setup.study_started.connect(start_study)
    app.aboutToQuit.connect(close_session)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
