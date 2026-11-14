from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from ui.theme import study_theme


class StudyCompleteWidget(QWidget):
    close_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("studyComplete")
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addStretch()

        card = QFrame()
        card.setObjectName("completionCard")
        card.setFixedWidth(650)
        content = QVBoxLayout(card)
        self.content = content
        content.setContentsMargins(36, 32, 36, 32)
        content.setSpacing(16)

        title = QLabel("Study complete")
        self.title = title
        title.setMinimumHeight(40)
        title.setObjectName("completionTitle")
        title.setAlignment(Qt.AlignCenter)
        content.addWidget(title)

        message = QLabel("Your final letter was submitted. Thank you for participating.")
        self.message = message
        message.setWordWrap(True)
        message.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        message.setAlignment(Qt.AlignCenter)
        content.addWidget(message)

        self.close_button = QPushButton("Close study")
        self.close_button.clicked.connect(self.close_requested.emit)
        content.addWidget(self.close_button, 0, Qt.AlignHCenter)

        layout.addWidget(card, 0, Qt.AlignHCenter)
        layout.addStretch()

        study_theme().changed.connect(self.apply_styles)
        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet(study_theme().stylesheet("""
            QWidget#studyComplete { background: $page; }
            QFrame#completionCard {
                background: $surface;
                border: 1px solid $border;
                border-top: 4px solid $brand;
                border-radius: 14px;
            }
            QLabel { color: $body; font-size: 14px; }
            QLabel#completionTitle { color: $heading; font-size: 26px; font-weight: bold; }
            QPushButton {
                background: $primary;
                color: $on_primary;
                border: 2px solid transparent;
                border-radius: 7px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background: $primary_hover; }
            QPushButton:focus { border-color: $accent_strong; }
        """))

