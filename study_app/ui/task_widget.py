
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal


class TaskWidget(QWidget):
    profile_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("taskWidget")
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # Header
        title = QLabel("PromptShield User Study")
        title.setObjectName("sidebarTitle")
        title.setWordWrap(True)

        subtitle = QLabel("AI-Assisted Writing Exercise")
        subtitle.setObjectName("sidebarSubtitle")

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        # Scrollable content
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        content = QWidget()
        content.setObjectName("taskContent")

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 8, 0)
        content_layout.setSpacing(20)

        # Task card
        task_card = QFrame()
        task_card.setObjectName("taskCard")

        task_layout = QVBoxLayout(task_card)
        task_layout.setContentsMargins(16, 16, 16, 16)
        task_layout.setSpacing(12)

        heading = QLabel("YOUR ASSIGNMENT")
        heading.setObjectName("cardHeading")

        self.task_title = QLabel("Financial Hardship Request")
        self.task_title.setObjectName("taskTitle")
        self.task_title.setWordWrap(True)

        self.task_description = QLabel()
        self.task_description.setObjectName("taskDescription")
        self.task_description.setWordWrap(True)

        task_layout.addWidget(heading)
        task_layout.addWidget(self.task_title)
        task_layout.addWidget(self.task_description)

        content_layout.addWidget(task_card)

        # Success criteria
        criteria_title = QLabel("What Makes a Strong Letter?")
        criteria_title.setObjectName("sectionTitle")
        criteria_title.setWordWrap(True)

        content_layout.addWidget(criteria_title)

        criteria = [
            "Clearly explain Maya's circumstances.",
            "Propose a realistic repayment plan.",
            "Include relevant supporting information.",
            "Use a professional and persuasive tone.",
        ]

        for criterion in criteria:
            label = QLabel("✓  " + criterion)
            label.setObjectName("criterionLabel")
            label.setWordWrap(True)
            content_layout.addWidget(label)

        # Profile access card
        profile_card = QFrame()
        profile_card.setObjectName("taskCard")

        profile_layout = QVBoxLayout(profile_card)
        profile_layout.setContentsMargins(16, 16, 16, 16)
        profile_layout.setSpacing(12)

        profile_heading = QLabel("CASE MATERIALS")
        profile_heading.setObjectName("cardHeading")

        profile_description = QLabel(
            "Review Maya's personal, employment, financial, "
            "medical, and housing information."
        )
        profile_description.setObjectName("taskDescription")
        profile_description.setWordWrap(True)

        self.profile_button = QPushButton("View Maya's Profile")
        self.profile_button.setObjectName("profileButton")
        self.profile_button.setCursor(Qt.PointingHandCursor)
        self.profile_button.clicked.connect(
            self.profile_requested.emit
        )

        profile_layout.addWidget(profile_heading)
        profile_layout.addWidget(profile_description)
        profile_layout.addWidget(self.profile_button)

        content_layout.addWidget(profile_card)
        content_layout.addStretch()

        self.scroll_area.setWidget(content)
        main_layout.addWidget(self.scroll_area, 1)

        # Safety instruction
        instructions = QLabel(
            "All case information is fictional. "
            "Use only the provided character information. "
            "Do not enter your own personal information."
        )
        instructions.setObjectName("instructionsLabel")
        instructions.setWordWrap(True)

        main_layout.addWidget(instructions)

    def set_task(self, task, task_number=1, task_count=1):
        """Update the assignment from the task configuration."""

        self.task_title.setText(
            task.get("title", "Financial Hardship Request")
        )

        self.task_description.setText(
            task.get("objective", "")
        )

        self.scroll_area.verticalScrollBar().setValue(0)

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget#taskWidget {
                background-color: #F8FAFC;
                color: #1E293B;
            }

            QWidget#taskWidget QLabel {
                background-color: transparent;
                color: #1E293B;
            }

            QWidget#taskContent {
                background-color: #F8FAFC;
            }

            QScrollArea {
                background-color: transparent;
                border: none;
            }

            QLabel#sidebarTitle {
                font-size: 20px;
                font-weight: bold;
                color: #1E293B;
            }

            QLabel#sidebarSubtitle {
                font-size: 12px;
                color: #64748B;
            }

            QLabel#sectionTitle {
                font-size: 15px;
                font-weight: bold;
                color: #1E293B;
            }

            QFrame#taskCard {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
            }

            QFrame#taskCard QLabel {
                background-color: transparent;
                border: none;
            }

            QLabel#cardHeading {
                font-size: 12px;
                font-weight: bold;
                color: #2563EB;
            }

            QLabel#taskTitle {
                font-size: 16px;
                font-weight: bold;
                color: #0F172A;
            }

            QLabel#taskDescription {
                font-size: 13px;
                color: #334155;
            }

            QLabel#criterionLabel {
                font-size: 13px;
                color: #334155;
            }

            QLabel#instructionsLabel {
                font-size: 12px;
                color: #64748B;
            }

            QPushButton#profileButton {
                background-color: #2563EB;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 12px;
                font-size: 13px;
                font-weight: bold;
            }

            QPushButton#profileButton:hover {
                background-color: #1D4ED8;
            }
        """)
