
import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QScrollArea,
    QTabWidget,
    QPushButton,
)


class ProfileWidget(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Maya Okafor - Character Profile")
        self.resize(650, 700)
        self.setMinimumSize(450, 450)

        self.profile_data = self.load_profile()

        self.setup_ui()
        self.apply_styles()

    def load_profile(self):
        config_path = (
            Path(__file__).resolve().parent.parent
            / "config"
            / "maya_okafor_profile.json"
        )

        with open(config_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        title = QLabel(self.profile_data["character"]["name"])
        title.setObjectName("profileTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Fictional Character Profile - Study Reference"
        )
        subtitle.setObjectName("profileSubtitle")
        layout.addWidget(subtitle)

        description = QLabel(
            self.profile_data["character"]["description"]
        )
        description.setObjectName("profileDescription")
        description.setWordWrap(True)
        layout.addWidget(description)

        # Profile tabs
        self.tabs = QTabWidget()
        self.tabs.setObjectName("profileTabs")

        sections = {
            "personal": "Personal",
            "employment": "Employment",
            "financial": "Financial",
            "medical": "Medical",
            "housing": "Housing",
        }

        for key, title in sections.items():
            section_data = self.profile_data["profile"][key]
            tab = self.create_profile_tab(section_data)
            self.tabs.addTab(tab, title)

        layout.addWidget(self.tabs, 1)

        # Footer
        footer = QHBoxLayout()

        note = QLabel("All information is fictional.")
        note.setObjectName("footerNote")

        close_button = QPushButton("Close")
        close_button.setObjectName("closeButton")
        close_button.clicked.connect(self.close)

        footer.addWidget(note)
        footer.addStretch()
        footer.addWidget(close_button)

        layout.addLayout(footer)

    def create_profile_tab(self, data):
        """Build a scrollable tab from profile fields."""

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        container.setObjectName("tabContent")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(12)

        for key, value in data.items():
            row = QFrame()
            row.setObjectName("profileRow")

            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(12, 10, 12, 10)
            row_layout.setSpacing(4)

            # Format JSON field names for display
            field_name = key.replace("_", " ").title()

            label = QLabel(field_name)
            label.setObjectName("fieldLabel")

            value_label = QLabel(
                self.format_value(key, value)
            )
            value_label.setObjectName("fieldValue")
            value_label.setWordWrap(True)
            value_label.setTextInteractionFlags(
                Qt.TextSelectableByMouse
            )

            row_layout.addWidget(label)
            row_layout.addWidget(value_label)

            layout.addWidget(row)

        layout.addStretch()

        scroll_area.setWidget(container)
        return scroll_area

    def format_value(self, key, value):
        """Format profile values for readability."""

        money_fields = {
            "normal_monthly_take_home_pay",
            "current_month_take_home_pay",
            "monthly_rent",
            "out_of_pocket_medical_expenses",
            "out_of_pocket_expenses",
            "amount_available_for_rent",
            "remaining_rent_balance",
            "savings_balance",
            "credit_card_balance",
            "amount_overdue_before_payment",
        }

        if key in money_fields and isinstance(value, (int, float)):
            return f"${value:,.2f}"

        return str(value)

    def apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #F8FAFC;
            }

            QLabel#profileTitle {
                font-size: 24px;
                font-weight: bold;
                color: #0F172A;
            }

            QLabel#profileSubtitle {
                font-size: 13px;
                color: #64748B;
            }

            QLabel#profileDescription {
                font-size: 13px;
                color: #334155;
            }

            QTabWidget::pane {
                border: 1px solid #E2E8F0;
                background-color: white;
                border-radius: 8px;
            }

            QTabBar::tab {
                background-color: #E2E8F0;
                color: #475569;
                padding: 10px 12px;
                font-size: 12px;
            }

            QTabBar::tab:selected {
                background-color: #2563EB;
                color: white;
            }

            QWidget#tabContent {
                background-color: white;
            }

            QScrollArea {
                background-color: white;
                border: none;
            }

            QFrame#profileRow {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
            }

            QLabel#fieldLabel {
                font-size: 12px;
                font-weight: bold;
                color: #64748B;
                background: transparent;
                border: none;
            }

            QLabel#fieldValue {
                font-size: 14px;
                color: #1E293B;
                background: transparent;
                border: none;
            }

            QLabel#footerNote {
                font-size: 12px;
                color: #64748B;
            }

            QPushButton#closeButton {
                background-color: #2563EB;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 10px 20px;
                font-weight: bold;
            }

            QPushButton#closeButton:hover {
                background-color: #1D4ED8;
            }
        """)
