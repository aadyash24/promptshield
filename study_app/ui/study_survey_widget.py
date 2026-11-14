"""Optional typed survey, saved only when the participant submits it."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QScrollArea, QFrame, QMessageBox,
)

from study.survey import MAX_RESPONSE_CHARS, questions_for
from ui.theme import study_theme


class StudySurveyWidget(QWidget):
    submitted = Signal(dict)
    skipped = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("studySurvey")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.fields = {}
        self.condition = None
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        title = QLabel("Letter submitted — Post-study survey")
        title.setObjectName("surveyTitle")
        title.setWordWrap(True)
        root.addWidget(title)
        note = QLabel(
            "Answer as yourself about your experience playing Maya. Your typed answers "
            "will be saved with your study session when you select Submit survey. "
            "Each question is optional; you can also skip the survey. "
            "Do not include real personal information about yourself or anyone else."
        )
        note.setWordWrap(True)
        root.addWidget(note)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        root.addWidget(self.scroll, 1)
        self.error_label = QLabel()
        self.error_label.setObjectName("surveyError")
        self.error_label.setWordWrap(True)
        root.addWidget(self.error_label)
        actions = QHBoxLayout()
        self.skip_button = QPushButton("Skip survey")
        self.skip_button.clicked.connect(self.skip_survey)
        self.submit_button = QPushButton("Submit survey")
        self.submit_button.setObjectName("surveySubmit")
        self.submit_button.clicked.connect(self.submit_survey)
        actions.addWidget(self.skip_button)
        actions.addStretch()
        actions.addWidget(self.submit_button)
        root.addLayout(actions)
        study_theme().changed.connect(self.apply_styles)
        self.apply_styles()

    def set_condition(self, condition):
        self.condition = condition
        self.fields = {}
        old = self.scroll.takeWidget()
        if old is not None:
            old.deleteLater()
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setSpacing(12)
        for index, (key, question) in enumerate(questions_for(condition), 1):
            label = QLabel(f"{index}. {question}")
            label.setWordWrap(True)
            label.setTextFormat(Qt.PlainText)
            edit = QPlainTextEdit()
            edit.setAccessibleName(question)
            edit.setPlaceholderText(f"Optional — up to {MAX_RESPONSE_CHARS:,} characters")
            edit.setFixedHeight(105)
            edit.textChanged.connect(lambda: self.error_label.clear())
            label.setBuddy(edit)
            layout.addWidget(label)
            layout.addWidget(edit)
            self.fields[key] = edit
        layout.addStretch()
        self.scroll.setWidget(body)
        self.error_label.clear()
        self.set_busy(False)

    def set_busy(self, busy):
        self.submit_button.setEnabled(not busy)
        self.skip_button.setEnabled(not busy)

    def submit_survey(self):
        answers = {key: edit.toPlainText().strip() for key, edit in self.fields.items()}
        for key, answer in answers.items():
            if len(answer) > MAX_RESPONSE_CHARS:
                self.error_label.setText(f"Please shorten your answer to {MAX_RESPONSE_CHARS:,} characters before submitting. Your answers have not been saved yet.")
                self.scroll.ensureWidgetVisible(self.fields[key])
                self.fields[key].setFocus()
                return
        self.set_busy(True)
        self.submitted.emit(answers)

    def skip_survey(self):
        if any(edit.toPlainText().strip() for edit in self.fields.values()):
            result = QMessageBox.question(
                self, "Skip survey?", "Your typed survey answers will not be saved. Skip the survey?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
            )
            if result != QMessageBox.Yes:
                return
        self.set_busy(True)
        self.skipped.emit()

    def save_failed(self):
        self.set_busy(False)
        self.error_label.setText("The survey could not be saved. Your answers are still here. Please ask the researcher for help, then try submitting again.")

    def clear_responses(self):
        for edit in self.fields.values():
            edit.clear()

    def apply_styles(self):
        self.setStyleSheet(study_theme().stylesheet("""
            QWidget#studySurvey, QScrollArea, QScrollArea > QWidget > QWidget { background: $page; }
            QLabel { color: $body; font-size: 14px; }
            QLabel#surveyTitle { color: $heading; font-size: 24px; font-weight: bold; border-top: 4px solid $brand; padding-top: 12px; }
            QLabel#surveyError { color: $status_error; }
            QPlainTextEdit { color: $text; background: $editor; border: 1px solid $control_border; border-radius: 8px; padding: 10px; font-size: 14px; selection-background-color: $selection; }
            QPlainTextEdit:focus { border-color: $accent; }
            QPushButton { background: $subtle; color: $text; border: 1px solid $control_border; border-radius: 7px; padding: 10px 18px; }
            QPushButton:hover { background: $hover; }
            QPushButton#surveySubmit { background: $primary; color: $on_primary; }
            QPushButton:focus { border: 2px solid $accent_strong; }
            QPushButton:disabled { background: $disabled_surface; color: $muted; }
        """))
