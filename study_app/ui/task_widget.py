from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ui.theme import study_theme


class TaskWidget(QWidget):
    profile_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("taskWidget")
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 12, 24, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        self.task_title = QLabel()
        self.task_title.setObjectName("taskTitle")
        self.task_title.setWordWrap(True)
        self.task_title.setTextFormat(Qt.PlainText)
        header.addWidget(self.task_title, 1)

        self.details_button = QPushButton()
        self.details_button.setCheckable(True)
        self.details_button.toggled.connect(self.set_details_visible)
        header.addWidget(self.details_button)

        self.profile_button = QPushButton("Your Profile (Maya)")
        self.profile_button.clicked.connect(self.profile_requested.emit)
        header.addWidget(self.profile_button)
        layout.addLayout(header)

        self.task_description = QLabel()
        self.task_description.setObjectName("taskDescription")
        self.task_description.setTextFormat(Qt.PlainText)
        self.task_description.setWordWrap(True)
        layout.addWidget(self.task_description)

        steps = QLabel("Review your profile  →  Plan and draft with AI  →  Check and submit")
        steps.setObjectName("taskDescription")
        steps.setWordWrap(True)
        layout.addWidget(steps)

        self.details_button.setChecked(True)
        study_theme().changed.connect(self.apply_styles)
        self.apply_styles()

    def set_details_visible(self, visible):
        self.task_description.setVisible(visible)
        self.details_button.setText("Hide task details" if visible else "Show task details")

    def set_task(self, task, task_number=1, task_count=1):
        self.task_title.setText(task.get("title", "Financial Hardship Request"))
        self.task_description.setText(task.get("objective", ""))
        self.details_button.setChecked(True)

    def apply_styles(self):
        self.setStyleSheet(study_theme().stylesheet("""
            QWidget#taskWidget {
                background-color: $surface;
                border: 1px solid $border;
                border-top: 4px solid $brand;
                border-radius: 14px;
            }
            QLabel#taskTitle {
                font-size: 18px;
                font-weight: bold;
                color: $heading;
            }
            QLabel#taskDescription {
                font-size: 14px;
                color: $body;
            }
            QPushButton {
                background-color: $subtle;
                color: $text;
                border: 1px solid $control_border;
                border-radius: 6px;
                padding: 7px 12px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: $hover; }
            QPushButton:focus { border-color: $accent; }
            QPushButton:checked { background-color: $selection; }
        """))
