import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

# Make the sibling ps package available when this file is run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ui.main_window import MainWindow
from ui.theme import study_theme


def main():
    app = QApplication(sys.argv)

    study_theme()

    window = MainWindow()
    app.aboutToQuit.connect(window.chat_panel.shutdown)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
