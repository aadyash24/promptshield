import sys

from PySide6.QtWidgets import QApplication

from PySide6.QtCore import Qt
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    # Force the light color scheme
    app.styleHints().setColorScheme(Qt.ColorScheme.Light)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()