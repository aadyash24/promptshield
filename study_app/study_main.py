"""PromptShield study launcher and event logging."""

import os
import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QStackedWidget,
)
from PySide6.QtCore import Qt, QTimer

# Make the sibling ps package available when this file is run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ui.main_window import MainWindow
from ui.promptshield_setup_widget import PromptShieldSetupWidget
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

    installation = PromptShieldSetupWidget()
    window.addWidget(installation)
    setup = StudySetupWidget()
    window.addWidget(setup)

    session = {
        "logger": None,
        "study": None,
        "completed": False,
        "message_count": 0,
    }
    ollama_model = ""

    def configure_models(study):
        chat = study.chat_panel
        chat.rewriter.model = ollama_model
        if "PROMPTSHIELD_CHAT_URL" not in os.environ and "PROMPTSHIELD_CHAT_MODEL" not in os.environ:
            chat.chat_backend.model = ollama_model

    def services_ready(model):
        nonlocal ollama_model
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
            app_version="prototype-v1",
            warning_hover_tracking=True,
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
    installation.service_lost.connect(lambda: window.setCurrentWidget(installation))
    app.aboutToQuit.connect(close_session)
    app.aboutToQuit.connect(installation.shutdown)

    window.show()
    QTimer.singleShot(0, installation.start)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
