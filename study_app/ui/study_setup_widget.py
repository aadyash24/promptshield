from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QCheckBox, QFrame, QStackedWidget, QScrollArea,
    QMessageBox, QSizePolicy,
)


class StudySetupWidget(QWidget):
    """Researcher setup followed by participant-facing study information."""

    study_started = Signal(str, str)  # participant_id, condition

    def __init__(self, parent=None):
        super().__init__(parent)
        self.participant_id = None
        self.condition = None
        self.setObjectName("studySetup")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.addStretch()

        self.pages = QStackedWidget()
        self.pages.setMaximumWidth(720)
        self.pages.addWidget(self._researcher_page())
        self.pages.addWidget(self._participant_page())
        root.addWidget(self.pages, alignment=Qt.AlignHCenter)
        root.addStretch()

    def _card(self, title, subtitle):
        card = QFrame()
        card.setObjectName("setupCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)
        heading = QLabel(title)
        heading.setObjectName("setupHeading")
        heading.setWordWrap(True)
        description = QLabel(subtitle)
        description.setObjectName("setupSubtitle")
        description.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(description)
        return card, layout

    def _researcher_page(self):
        card, layout = self._card(
            "Researcher setup",
            "Complete this step before handing the computer to the participant."
        )
        label = QLabel("Participant ID")
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("e.g., K-P001")
        self.id_input.setMaxLength(40)
        self.id_input.returnPressed.connect(self._continue_to_consent)
        layout.addWidget(label)
        layout.addWidget(self.id_input)

        label = QLabel("Study condition")
        self.condition_combo = QComboBox()
        self.condition_combo.addItem("Active — show privacy feedback", "active")
        self.condition_combo.addItem("Silent — detection without feedback", "silent")
        self.condition_combo.addItem("Development — warnings enabled, no logging", "dev")
        layout.addWidget(label)
        layout.addWidget(self.condition_combo)

        note = QLabel(
            "Assign a unique ID across your team. Follow your agreed allocation "
            "schedule rather than choosing a condition based on the participant. "
            "This screen is for researchers only."
        )
        note.setObjectName("finePrint")
        note.setWordWrap(True)
        layout.addWidget(note)

        button = QPushButton("Continue to participant information")
        button.setObjectName("primaryButton")
        button.clicked.connect(self._continue_to_consent)
        layout.addWidget(button)
        return card

    def _participant_page(self):
        card, layout = self._card(
            "Welcome to the AI Writing Study",
            "Please read this information before deciding whether to participate."
        )
        self.participant_label = QLabel("Participant ID: —")
        self.participant_label.setObjectName("finePrint")
        layout.addWidget(self.participant_label)

        scroll = QScrollArea()
        scroll.setObjectName("disclosureScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setMinimumHeight(270)
        scroll.setMaximumHeight(390)

        disclosure = QWidget()
        disclosure_layout = QVBoxLayout(disclosure)
        disclosure_layout.setContentsMargins(4, 4, 12, 4)
        disclosure_layout.setSpacing(12)

        sections = [
            ("What you will do", "You will use an AI assistant and a document editor to write a letter for a fictional character. You may review the character's provided case materials and decide which details to use."),
            ("Privacy feedback", "The application may examine text as you type to identify potentially sensitive information. Some participants may see visual privacy guidance, and others may not. This does not prevent you from completing the task."),
            ("Information used", "The case details are fictional. Do not enter your own real personal, medical, or financial information, or information about other real people."),
            (
                "Data handling",
                "The study application records interaction timestamps, "
                "privacy detection categories and severity levels, "
                "warning interactions, and task completion information. "
                "The research event logger is designed not to store the "
                "text you type. Ask the researcher about data storage, "
                "access, retention, other application components, and "
                "any external AI service before consenting."
            ),
            ("Your choice", "Participation is voluntary. You can decline to begin or stop at any time. Ask the researcher about the withdrawal procedure and whether already collected data can be removed."),
        ]
        for name, description in sections:
            heading = QLabel(name)
            heading.setObjectName("sectionHeading")
            body = QLabel(description)
            body.setObjectName("bodyText")
            body.setWordWrap(True)
            disclosure_layout.addWidget(heading)
            disclosure_layout.addWidget(body)
        disclosure_layout.addStretch()
        scroll.setWidget(disclosure)
        layout.addWidget(scroll)

        self.consent_box = QCheckBox(
            "I have read the study information and voluntarily agree to participate."
        )
        self.consent_box.stateChanged.connect(self._update_begin_button)
        layout.addWidget(self.consent_box)

        actions = QHBoxLayout()
        decline = QPushButton("Decline / Exit")
        decline.setObjectName("secondaryButton")
        decline.clicked.connect(self._decline)
        self.begin_button = QPushButton("Begin Writing Exercise")
        self.begin_button.setObjectName("primaryButton")
        self.begin_button.setEnabled(False)
        self.begin_button.clicked.connect(self._begin)
        actions.addWidget(decline)
        actions.addStretch()
        actions.addWidget(self.begin_button)
        layout.addLayout(actions)
        return card


    def _continue_to_consent(self):
        condition = self.condition_combo.currentData()

        # Development mode skips registration and consent.
        # It must never create research data.
        if condition == "dev":
            self.participant_id = "DEV"
            self.condition = "dev"
            self.study_started.emit("DEV", "dev")
            return

        participant_id = self.id_input.text().strip()

        if not participant_id or not all(
            ch.isalnum() or ch in "-_"
            for ch in participant_id
        ):
            QMessageBox.warning(
                self,
                "Participant ID required",
                "Enter a non-empty ID using letters, numbers, "
                "hyphens, or underscores."
            )
            self.id_input.setFocus()
            return

        self.participant_id = participant_id
        self.condition = condition

        self.participant_label.setText(
            f"Participant ID: {participant_id}"
        )

        self.consent_box.setChecked(False)
        self.pages.setCurrentIndex(1)


    def _update_begin_button(self):
        self.begin_button.setEnabled(self.consent_box.isChecked())

    def _begin(self):
        if self.consent_box.isChecked() and self.participant_id is not None:
            self.study_started.emit(self.participant_id, self.condition)

    def _decline(self):
        self.window().close()

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget#studySetup { background: #F8FAFC; color: #1E293B; }
            QFrame#setupCard { background: white; border: 1px solid #E2E8F0;
                               border-radius: 14px; }
            QFrame#setupCard QLabel { background: transparent; border: none; }
            QLabel#setupHeading { font-size: 23px; font-weight: bold; color: #0F172A; }
            QLabel#setupSubtitle { font-size: 13px; color: #64748B; }
            QLabel#sectionHeading { font-size: 13px; font-weight: bold; color: #1D4ED8; }
            QLabel#bodyText { font-size: 13px; color: #334155; }
            QLabel#finePrint { font-size: 12px; color: #64748B; }
            QScrollArea#disclosureScroll { border: 1px solid #E2E8F0;
                                           border-radius: 8px; background: #FFFFFF; }
            QLineEdit, QComboBox { background: #F8FAFC; border: 1px solid #CBD5E1;
                                   border-radius: 7px; padding: 10px; color: #0F172A; }
            QCheckBox { spacing: 10px; font-size: 13px; color: #334155; }
            QPushButton { padding: 12px 14px; border-radius: 7px;
                          font-size: 12px; font-weight: bold; }
            QPushButton#primaryButton { background: #2563EB; color: white; border: none; }
            QPushButton#primaryButton:hover { background: #1D4ED8; }
            QPushButton#primaryButton:disabled { background: #CBD5E1; color: #64748B; }
            QPushButton#secondaryButton { background: white; color: #475569;
                                          border: 1px solid #CBD5E1; }
        """)
