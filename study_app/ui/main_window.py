
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QSplitter,
    QToolButton,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap

from ui.task_widget import TaskWidget
from ui.chat_widget import ChatWidget
from ui.document_widget import DocumentWidget
from ui.profile_widget import ProfileWidget
from ui.server_status import ServerStatus
from ui.theme import study_theme

from study.tasks import TaskManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PromptShield - User Study")
        self.resize(1500, 850)
        self.setMinimumSize(1100, 650)

        self.task_manager = TaskManager()

        self.setup_ui()

        self.profile_window = ProfileWidget(self)

        self.task_panel.profile_requested.connect(
            self.show_profile
        )

    def setup_ui(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Main horizontal splitter
        self.splitter = QSplitter(Qt.Horizontal)

        # Left: task instructions
        self.task_panel = TaskWidget()
        self.task_panel.set_task(
            self.task_manager.current_task,
            self.task_manager.task_number,
            self.task_manager.task_count
        )

        # Right: letter editor
        self.document_panel = DocumentWidget()

        self.document_panel.document_submitted.connect(
            self.on_document_submitted
        )

        # Center: AI chat
        self.chat_panel = ChatWidget()
        status_bar = self.statusBar()
        self.theme_button = QToolButton()
        self.theme_button.setObjectName("themeToggle")
        self.theme_button.setFixedSize(28, 28)
        self.theme_button.setCursor(Qt.PointingHandCursor)
        self.theme_button.setFocusPolicy(Qt.StrongFocus)
        self.theme_button.setCheckable(True)
        theme = study_theme()
        self.theme_button.toggled.connect(theme.set_dark)
        theme.changed.connect(self.update_theme_button)
        self.update_theme_button()
        status_bar.addWidget(self.theme_button)
        status_bar.addPermanentWidget(ServerStatus(
            self.chat_panel.detector.base_url, self.chat_panel.rewriter,
        ))

        self.splitter.addWidget(self.task_panel)
        self.splitter.addWidget(self.chat_panel)
        self.splitter.addWidget(self.document_panel)

        # Initial widths for the task, chat, and letter editor.
        self.splitter.setSizes([375, 525, 600])

        # Allow all panels to resize
        for i in range(3):
            self.splitter.setStretchFactor(i, 1)

        # Minimum panel widths
        self.task_panel.setMinimumWidth(260)
        self.document_panel.setMinimumWidth(350)
        self.chat_panel.setMinimumWidth(350)

        main_layout.addWidget(self.splitter)

    def update_theme_button(self):
        theme = study_theme()
        label = "Switch to light mode" if theme.dark else "Switch to dark mode"
        self.theme_button.setChecked(theme.dark)
        self.theme_button.setAccessibleName(label)
        self.theme_button.setToolTip(label)
        self.theme_button.setStyleSheet(theme.stylesheet("""
            QToolButton { background: transparent; border: 1px solid transparent; border-radius: 6px; }
            QToolButton:hover { background: $hover; }
            QToolButton:focus { border-color: $accent; }
        """))
        icon = QPixmap(18, 18)
        icon.fill(Qt.transparent)
        with QPainter(icon) as painter:
            painter.setRenderHint(QPainter.Antialiasing)
            color = QColor(theme.colors["body"])
            if theme.dark:
                painter.setPen(color)
                painter.drawEllipse(6, 6, 6, 6)
                for x, y in ((1, 0), (0, 1), (-1, 0), (0, -1),
                             (1, 1), (-1, -1), (1, -1), (-1, 1)):
                    painter.drawLine(9 + 5 * x, 9 + 5 * y, 9 + 7 * x, 9 + 7 * y)
            else:
                painter.setPen(Qt.NoPen)
                painter.setBrush(color)
                painter.drawEllipse(2, 3, 13, 13)
                painter.setCompositionMode(QPainter.CompositionMode_Clear)
                painter.drawEllipse(7, 0, 12, 12)
        self.theme_button.setIcon(QIcon(icon))

    def show_profile(self):
        self.profile_window.show()
        self.profile_window.raise_()
        self.profile_window.activateWindow()

    def on_document_submitted(self, text):
        print("Final document submitted!")
        print(f"Word count: {len(text.split())}")
