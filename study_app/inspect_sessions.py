import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from ui.session_results_widget import SessionResultsWindow


def main():
    app = QApplication(sys.argv)

    app.styleHints().setColorScheme(
        Qt.ColorScheme.Light
    )

    window = SessionResultsWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
