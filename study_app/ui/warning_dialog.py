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
        self.setFixedWidth(420)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(10)

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
        intro = QLabel("Choose why you want to hide this warning.")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        layout.addSpacing(8)

        self.wrong_button = self.add_choice(
            layout, "Not sensitive", "This was flagged incorrectly. Mark it as non-PII.", "misdetected"
        )
        layout.addSpacing(6)
        self.ignore_button = self.add_choice(
            layout, "Ignore warning", "Hide the warning, but keep it classified as sensitive.", "ignore"
        )
        layout.addSpacing(10)
        note = QLabel("The warning may return if you edit this sentence.")
        note.setWordWrap(True)
        note.setObjectName("dismissNote")
        layout.addWidget(note)
        layout.addSpacing(8)
        footer = QHBoxLayout()
        footer.addStretch()
        self.cancel_button = QPushButton("Go back")
        self.cancel_button.setObjectName("dismissCancel")
        self.cancel_button.setDefault(True)
        self.cancel_button.clicked.connect(self.reject)
        footer.addWidget(self.cancel_button)
        layout.addLayout(footer)
        study_theme().changed.connect(self.apply_styles)
        self.apply_styles()
        self.cancel_button.setFocus()

    def add_choice(self, layout, title, explanation, reason):
        button = QPushButton(title)
        button.setCursor(Qt.PointingHandCursor)
        button.setAutoDefault(False)
        button.clicked.connect(lambda: self.select(reason))
        layout.addWidget(button)
        label = QLabel(explanation)
        label.setWordWrap(True)
        label.setObjectName("choiceDescription")
        layout.addWidget(label)
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
            QLabel#choiceDescription { color: $muted; font-size: 12px; padding: 0 2px; }
            QLabel#dismissNote { color: $muted; font-size: 12px; }
            QPushButton { background: $subtle; color: $text; border: 1px solid $border;
                border-radius: 8px; padding: 11px 14px; font-size: 14px; font-weight: 600; text-align: left; }
            QPushButton:hover { background: $hover; border-color: $strong_border; }
            QPushButton:focus { border-color: $accent_strong; }
            QPushButton:pressed { background: $selection; }
            QPushButton#dismissCancel { background: $surface; font-size: 13px;
                font-weight: normal; text-align: center; padding: 8px 18px; }
        """))
