import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from ui.study_overview_widget import StudyOverviewWindow


def main():
    app = QApplication(sys.argv)

    app.styleHints().setColorScheme(
        Qt.ColorScheme.Light
    )

    window = StudyOverviewWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()