
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


class DocumentWidget(QWidget):
    document_submitted = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("documentWidget")
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.is_submitted = False

        self.setup_ui()
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
        self.setStyleSheet("""
            QWidget#documentWidget {
                background-color: #FFFFFF;
            }

            QLabel#editorTitle {
                font-size: 20px;
                font-weight: bold;
                color: #0F172A;
            }

            QLabel#wordCount {
                font-size: 12px;
                color: #64748B;
            }

            QLabel#editorInstructions {
                font-size: 13px;
                color: #64748B;
            }

            QPlainTextEdit#letterEditor {
                background-color: #FAFBFD;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                border-radius: 10px;
                padding: 16px;
                font-size: 14px;
                selection-background-color: #BFDBFE;
            }

            QPlainTextEdit#letterEditor:focus {
                border: 1px solid #2563EB;
            }

            QPushButton {
                border-radius: 7px;
                padding: 10px 14px;
                font-size: 12px;
                font-weight: bold;
            }

            QPushButton#clearButton {
                background-color: #F1F5F9;
                color: #475569;
                border: 1px solid #E2E8F0;
            }

            QPushButton#clearButton:hover {
                background-color: #E2E8F0;
            }

            QPushButton#submitButton {
                background-color: #2563EB;
                color: white;
                border: none;
            }

            QPushButton#submitButton:hover {
                background-color: #1D4ED8;
            }

            QPushButton#submitButton:disabled {
                background-color: #94A3B8;
            }
        """)
