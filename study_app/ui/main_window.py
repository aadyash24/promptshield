
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QSplitter,
    QFrame,
)
from PySide6.QtCore import Qt

from ui.task_widget import TaskWidget
from ui.chat_widget import ChatWidget
from ui.document_widget import DocumentWidget
from ui.profile_widget import ProfileWidget

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

        # Center: temporary document editor placeholder
        self.document_panel = DocumentWidget()

        self.document_panel.document_submitted.connect(
            self.on_document_submitted
        )

        # Right: AI chat
        self.chat_panel = ChatWidget()

        self.chat_panel.insert_requested.connect(
            self.document_panel.insert_text
        )

        self.chat_panel.replace_requested.connect(
            self.replace_document
        )

        self.splitter.addWidget(self.task_panel)
        self.splitter.addWidget(self.document_panel)
        self.splitter.addWidget(self.chat_panel)

        # Initial proportions: 25% / 40% / 35%
        self.splitter.setSizes([375, 600, 525])

        # Allow all panels to resize
        for i in range(3):
            self.splitter.setStretchFactor(i, 1)

        # Minimum panel widths
        self.task_panel.setMinimumWidth(260)
        self.document_panel.setMinimumWidth(350)
        self.chat_panel.setMinimumWidth(350)

        main_layout.addWidget(self.splitter)

        
        # Temporary sample response for testing editor integration
        self.chat_panel.add_message(
            "Dear Jordan Ellis,\n\n"
            "I am writing to request a temporary payment arrangement "
            "for my November rent. Due to unexpected circumstances, "
            "I am unable to pay the full amount by the original due date.\n\n"
            "I would appreciate your consideration of a short-term "
            "repayment arrangement.\n\n"
            "Sincerely,\n"
            "Maya Okafor",
            sender="assistant"
        )


    def show_profile(self):
        self.profile_window.show()
        self.profile_window.raise_()
        self.profile_window.activateWindow()

    def on_document_submitted(self, text):
        print("Final document submitted!")
        print(f"Word count: {len(text.split())}")

        
    def replace_document(self, text):
        """Replace the document with an AI-generated response."""

        from PySide6.QtWidgets import QMessageBox

        if self.document_panel.is_submitted:
            return

        # No confirmation necessary if the editor is empty
        if not self.document_panel.get_document().strip():
            self.document_panel.set_document(text)
            return

        response = QMessageBox.question(
            self,
            "Replace Draft",
            "Replace your current letter with this AI response? "
            "Your existing draft will be overwritten.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if response == QMessageBox.Yes:
            self.document_panel.set_document(text)
