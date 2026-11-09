"""Launch the study after researcher setup and participant consent."""
import sys
from PySide6.QtWidgets import QApplication, QStackedWidget
from PySide6.QtCore import Qt
from ui.main_window import MainWindow
from ui.study_setup_widget import StudySetupWidget


def main():
    app = QApplication(sys.argv)
    app.styleHints().setColorScheme(Qt.ColorScheme.Light)

    study_window = QStackedWidget()
    study_window.setWindowTitle("PromptShield User Study")
    study_window.resize(1500, 850)

    setup = StudySetupWidget()
    study_window.addWidget(setup)

    def start_study(participant_id, condition):
        study = MainWindow()
        study.participant_id = participant_id
        study.study_condition = condition
        # Live detector remains enabled in both conditions.
        study.chat_panel.set_study_condition(condition)
        study_window.addWidget(study)
        study_window.setCurrentWidget(study)
        study_window.setWindowTitle("PromptShield — Writing Exercise")

    setup.study_started.connect(start_study)
    study_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
