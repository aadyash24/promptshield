from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton

from ui.theme import study_theme


def warning_category_title(category):
    category = str(category or "SENSITIVE").strip().upper()
    return {
        "FIN_INSTITUTION": "Financial institution",
        "MED_PROVIDER": "Medical provider",
        "MED_CONDITION": "Medical condition",
        "MED_RECORD_ID": "Medical record ID",
        "GOV_ID": "Government ID",
        "WORKPLACE_SCHOOL": "Workplace or school",
        "BALANCE_DEBT": "Balance or debt",
        "SENSITIVE": "Sensitive information",
    }.get(category, category.replace("_", " ").capitalize())


class WarningDismissDialog(QDialog):
    """A compact, consistently laid out choice rather than a native message box."""

    def __init__(self, parent=None, finding=None):
        super().__init__(parent)
        self.choice = None
        self.setWindowTitle("Dismiss warning")
        self.setObjectName("warningDismissDialog")
        self.setFixedWidth(460)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(12)

        if finding is not None:
            classification = QLabel(
                f"{warning_category_title(finding.get('category'))} · Tier {finding.get('tier', 1)}"
            )
            classification.setTextFormat(Qt.PlainText)
            classification.setWordWrap(True)
            classification.setObjectName("dismissClassification")
            layout.addWidget(classification)

        heading = QLabel("Dismiss this warning?")
        heading.setWordWrap(True)
        heading.setObjectName("dismissHeading")
        layout.addWidget(heading)
        intro = QLabel("Why are you dismissing it?")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        layout.addSpacing(2)

        self.wrong_button = self.add_choice(
            layout, "Incorrect detection",
            "This information is not sensitive.\nThe warning is wrong.", "misdetected"
        )
        self.ignore_button = self.add_choice(
            layout, "Ignore anyway",
            "I know this information is sensitive.\nI’m comfortable sharing it anyway.", "ignore"
        )
        layout.addSpacing(2)
        note = QLabel("The warning may return if you edit this sentence.")
        note.setWordWrap(True)
        note.setObjectName("dismissNote")
        layout.addWidget(note)
        layout.addSpacing(2)
        footer = QHBoxLayout()
        footer.addStretch()
        self.cancel_button = QPushButton("Keep warning")
        self.cancel_button.setAccessibleName("Keep warning")
        self.cancel_button.setObjectName("dismissCancel")
        self.cancel_button.setDefault(True)
        self.cancel_button.clicked.connect(self.reject)
        footer.addWidget(self.cancel_button)
        layout.addLayout(footer)
        study_theme().changed.connect(self.apply_styles)
        self.apply_styles()
        self.cancel_button.setFocus()

    def add_choice(self, layout, title, explanation, reason):
        button = QPushButton()
        button.setObjectName("dismissChoice")
        button.setAccessibleName(title)
        button.setAccessibleDescription(explanation.replace("\n", " "))
        button.setMinimumHeight(104)
        button.setCursor(Qt.PointingHandCursor)
        button.setAutoDefault(False)
        button.clicked.connect(lambda: self.select(reason))
        content = QVBoxLayout(button)
        content.setContentsMargins(16, 14, 16, 14)
        content.setSpacing(5)
        heading = QLabel(title)
        heading.setObjectName("choiceTitle")
        heading.setWordWrap(True)
        heading.setAttribute(Qt.WA_TransparentForMouseEvents)
        content.addWidget(heading)
        label = QLabel(explanation)
        label.setWordWrap(True)
        label.setObjectName("choiceDescription")
        label.setAttribute(Qt.WA_TransparentForMouseEvents)
        content.addWidget(label)
        layout.addWidget(button)
        return button

    def select(self, reason):
        self.choice = reason
        self.accept()

    def apply_styles(self):
        self.setStyleSheet(study_theme().stylesheet("""
            QDialog#warningDismissDialog { background: $surface; }
            QLabel { color: $body; font-size: 13px; background: transparent; border: none; }
            QLabel#dismissHeading { color: $heading; font-size: 20px; font-weight: 600; }
            QLabel#dismissClassification { color: $muted; font-size: 13px; font-weight: 600; }
            QLabel#choiceTitle { color: $heading; font-size: 15px; font-weight: 600; }
            QLabel#choiceDescription { color: $body; font-size: 13px; }
            QLabel#dismissNote { color: $muted; font-size: 12px; }
            QPushButton { background: $subtle; color: $text; border: 1px solid $border;
                border-radius: 8px; padding: 11px 14px; font-size: 14px; font-weight: 600; text-align: left; }
            QPushButton:hover { background: $hover; border-color: $strong_border; }
            QPushButton:focus { border-color: $accent_strong; }
            QPushButton:pressed { background: $selection; }
            QPushButton#dismissChoice { background: $surface; border: 1px solid $control_border;
                border-radius: 10px; padding: 0; }
            QPushButton#dismissChoice:hover { background: $subtle; border-color: $strong_border; }
            QPushButton#dismissChoice:focus { background: $subtle; border: 2px solid $accent_strong; }
            QPushButton#dismissChoice:pressed { background: $selection; }
            QPushButton#dismissCancel { background: $surface; font-size: 13px;
                font-weight: normal; text-align: center; padding: 8px 18px; }
        """))
