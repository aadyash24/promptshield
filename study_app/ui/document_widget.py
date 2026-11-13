
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal

from ui.theme import study_theme


class DocumentWidget(QWidget):
    document_submitted = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("documentWidget")
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.is_submitted = False

        self.setup_ui()
        study_theme().changed.connect(self.apply_styles)
        self.apply_styles()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()

        title = QLabel("Letter Editor")
        title.setObjectName("editorTitle")

        self.word_count = QLabel("0 words")
        self.word_count.setObjectName("wordCount")

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.word_count)

        layout.addLayout(header)

        # Instructions
        instructions = QLabel(
            "Draft your hardship request below. "
            "You can write directly or use suggestions from the AI assistant."
        )
        instructions.setObjectName("editorInstructions")
        instructions.setWordWrap(True)

        layout.addWidget(instructions)

        # Document editor
        self.editor = QPlainTextEdit()
        self.editor.setObjectName("letterEditor")
        self.editor.setPlaceholderText(
            "Dear Jordan Ellis,\n\n"
            "I am writing to request..."
        )
        self.editor.setUndoRedoEnabled(True)
        self.editor.textChanged.connect(self.update_word_count)

        layout.addWidget(self.editor, 1)

        # Bottom controls
        controls = QHBoxLayout()
        controls.setSpacing(12)

        self.clear_button = QPushButton("Clear Draft")
        self.clear_button.setObjectName("clearButton")
        self.clear_button.clicked.connect(self.clear_draft)

        self.submit_button = QPushButton("Submit Final Letter")
        self.submit_button.setObjectName("submitButton")
        self.submit_button.clicked.connect(self.submit_document)

        controls.addWidget(self.clear_button)
        controls.addStretch()
        controls.addWidget(self.submit_button)

        layout.addLayout(controls)

    def update_word_count(self):
        text = self.editor.toPlainText()
        count = len(text.split())
        self.word_count.setText(f"{count} words")

    def get_document(self):
        """Return the current document text."""
        return self.editor.toPlainText()

    def set_document(self, text):
        """Replace the document contents."""
        if self.is_submitted:
            return

        self.editor.setPlainText(text)

    def insert_text(self, text):
        """Insert text at the current cursor position."""
        if self.is_submitted:
            return

        self.editor.insertPlainText(text)

    def clear_draft(self):
        """Clear the editor after confirmation."""
        if self.is_submitted:
            return

        if not self.editor.toPlainText().strip():
            return

        response = QMessageBox.question(
            self,
            "Clear Draft",
            "Are you sure you want to clear your entire draft?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if response == QMessageBox.Yes:
            self.editor.clear()

    def submit_document(self):
        """Finalize the current document."""
        if self.is_submitted:
            return

        text = self.get_document().strip()

        if not text:
            QMessageBox.warning(
                self,
                "Empty Document",
                "Please write your letter before submitting."
            )
            return

        response = QMessageBox.question(
            self,
            "Submit Final Letter",
            "Are you sure you want to submit your final letter? "
            "You won't be able to edit it afterward.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if response != QMessageBox.Yes:
            return

        self.is_submitted = True
        self.editor.setReadOnly(True)

        self.submit_button.setEnabled(False)
        self.submit_button.setText("Submitted")
        self.clear_button.setEnabled(False)

        self.document_submitted.emit(text)

    def apply_styles(self):
        self.setStyleSheet(study_theme().stylesheet("""
            QWidget#documentWidget {
                background-color: $surface;
            }

            QLabel#editorTitle {
                font-size: 20px;
                font-weight: bold;
                color: $heading;
            }

            QLabel#wordCount {
                font-size: 12px;
                color: $muted;
            }

            QLabel#editorInstructions {
                font-size: 13px;
                color: $muted;
            }

            QPlainTextEdit#letterEditor {
                background-color: $editor;
                color: $text;
                border: 1px solid $control_border;
                border-radius: 10px;
                padding: 16px;
                font-size: 14px;
                selection-background-color: $selection;
                selection-color: $heading;
            }

            QPlainTextEdit#letterEditor:focus {
                border: 1px solid $accent;
            }

            QPushButton {
                border-radius: 7px;
                padding: 10px 14px;
                font-size: 12px;
                font-weight: bold;
            }

            QPushButton#clearButton {
                background-color: $subtle;
                color: $secondary;
                border: 1px solid $border;
            }

            QPushButton#clearButton:hover {
                background-color: $hover;
            }

            QPushButton#submitButton {
                background-color: $primary;
                color: $on_primary;
                border: none;
            }

            QPushButton#submitButton:hover {
                background-color: $primary_hover;
            }

            QPushButton#submitButton:disabled {
                background-color: $disabled;
            }
        """))
