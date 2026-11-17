"""Cross-session study inspector for analysis and participant drill-down."""

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QFileDialog, QFrame, QGridLayout, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMainWindow, QPlainTextEdit, QPushButton,
    QMenu, QSplitter, QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
    QWidgetAction,
)
from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT,
)
from matplotlib.figure import Figure

from analytics.session_data import DEFAULT_SESSIONS_DIR, discover_sessions, load_session
from analytics.study_analysis import analyze_session, session_analysis_details
from ui.theme import study_theme
from ui.warning_dialog import warning_category_title


EVENT_COLORS = {
    "Session": "#475569", "Detection": "#2563EB", "Warning": "#B45309",
    "Message": "#7E22CE", "Document": "#047857", "Survey": "#0F766E",
    "Other": "#64748B",
}


def event_group(event_type):
    return {
        "session": "Session", "consent": "Session", "task": "Session",
        "profile": "Session", "detection": "Detection", "warning": "Warning",
        "rewrite": "Warning", "message": "Message", "chat": "Message",
        "document": "Document", "post": "Survey",
    }.get(str(event_type or "").partition("_")[0], "Other")


def display(value, empty="—"):
    if value is None:
        return empty
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def breakdown_text(items):
    parts = []
    for item in items or []:
        tier = f" T{item.get('tier')}" if item.get("tier") else ""
        parts.append(
            f"{warning_category_title(item.get('category'))}{tier} ×{item.get('count', 1)}"
        )
    return ", ".join(parts) or "—"


class ParticipantFilter(QPushButton):
    selectionChanged = Signal()

    def __init__(self):
        super().__init__("All participants")
        self.setMinimumWidth(150)
        self.setMenu(QMenu(self))
        self.checkboxes = {}

    def selected_values(self):
        return {value for value, box in self.checkboxes.items() if box.isChecked()}

    def set_options(self, values, selected):
        self.menu().clear()
        self.checkboxes.clear()
        clear = self.menu().addAction("All participants")
        clear.triggered.connect(self.clear_selection)
        self.menu().addSeparator()
        for value in values:
            box = QCheckBox(value, self.menu())
            box.setChecked(value in selected)
            action = QWidgetAction(self.menu())
            action.setDefaultWidget(box)
            self.menu().addAction(action)
            self.checkboxes[value] = box
            box.toggled.connect(self.selection_changed)
        self.update_label()

    def clear_selection(self):
        for box in self.checkboxes.values():
            box.blockSignals(True)
            box.setChecked(False)
            box.blockSignals(False)
        self.selection_changed()

    def update_label(self):
        values = sorted(self.selected_values())
        self.setText(values[0] if len(values) == 1 else
                     f"{len(values)} participants" if values else "All participants")
        self.setToolTip(", ".join(values) or "All participants")

    def selection_changed(self):
        self.update_label()
        self.selectionChanged.emit()


class MetricCard(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setObjectName("metricCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(2)
        label = QLabel(title)
        label.setObjectName("metricTitle")
        self.value = QLabel("—")
        self.value.setObjectName("metricValue")
        layout.addWidget(label)
        layout.addWidget(self.value)

    def set_value(self, value):
        self.value.setText(display(value))


class SortableItem(QTableWidgetItem):
    def __lt__(self, other):
        left = self.data(Qt.UserRole)
        right = other.data(Qt.UserRole)
        if left is None:
            return right is not None
        if right is None:
            return False
        try:
            return left < right
        except TypeError:
            return str(left).lower() < str(right).lower()


class StudyOverviewWindow(QMainWindow):
    def __init__(self, sessions_dir=DEFAULT_SESSIONS_DIR):
        super().__init__()
        self.sessions_dir = Path(sessions_dir)
        self.entries = []
        self.filtered_entries = []
        self.filtered_events = []
        self.setWindowTitle("PromptShield — Study Inspector")
        available = self.screen().availableGeometry()
        self.resize(min(1720, available.width() - 30), min(1050, available.height() - 60))
        self.setMinimumSize(1050, 700)
        self.setup_ui()
        study_theme().changed.connect(self.apply_styles)
        self.apply_styles()
        self.refresh_data()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 14, 16, 16)
        root.setSpacing(12)
        header = QHBoxLayout()
        titles = QVBoxLayout()
        title = QLabel("Study Inspector")
        title.setObjectName("pageTitle")
        self.subtitle = QLabel(str(self.sessions_dir))
        self.subtitle.setObjectName("mutedText")
        self.subtitle.setWordWrap(True)
        titles.addWidget(title)
        titles.addWidget(self.subtitle)
        header.addLayout(titles, 1)
        choose = QPushButton("Choose folder")
        choose.clicked.connect(self.choose_folder)
        export = QPushButton("Export filtered data")
        export.clicked.connect(self.export_filtered_data)
        refresh = QPushButton("Refresh")
        refresh.setObjectName("primaryButton")
        refresh.clicked.connect(self.refresh_data)
        header.addWidget(choose)
        header.addWidget(export)
        header.addWidget(refresh)
        root.addLayout(header)

        filters = QFrame()
        filters.setObjectName("filterBar")
        bar = QHBoxLayout(filters)
        bar.setContentsMargins(12, 9, 12, 9)
        bar.setSpacing(9)
        self.task_filter = self.add_filter(bar, "Task")
        self.condition_filter = self.add_filter(bar, "Condition")
        bar.addWidget(QLabel("Participants"))
        self.participant_filter = ParticipantFilter()
        self.participant_filter.selectionChanged.connect(self.apply_filters)
        bar.addWidget(self.participant_filter)
        self.session_filter = self.add_filter(bar, "Session")
        self.sort_divider = QFrame()
        self.sort_divider.setObjectName("filterDivider")
        self.sort_divider.setFrameShape(QFrame.VLine)
        bar.addWidget(self.sort_divider)
        self.sort_label = QLabel("Sort by")
        bar.addWidget(self.sort_label)
        self.sort_filter = QComboBox()
        self.sort_filter.setMinimumWidth(145)
        self.sort_filter.currentIndexChanged.connect(self.apply_sort)
        bar.addWidget(self.sort_filter)
        self.sort_order = QComboBox()
        self.sort_order.addItem("Ascending", Qt.AscendingOrder)
        self.sort_order.addItem("Descending", Qt.DescendingOrder)
        self.sort_order.currentIndexChanged.connect(self.apply_sort)
        bar.addWidget(self.sort_order)
        bar.addStretch()
        self.filter_status = QLabel()
        self.filter_status.setObjectName("mutedText")
        bar.addWidget(self.filter_status)
        root.addWidget(filters)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        root.addWidget(self.tabs, 1)
        self.setup_overview_tab()
        self.setup_messages_tab()
        self.setup_categories_tab()
        self.setup_survey_tab()
        self.setup_events_tab()
        self.setup_charts_tab()
        self.tabs.currentChanged.connect(self.refresh_sort_options)
        self.refresh_sort_options(0)

    def add_filter(self, layout, text):
        layout.addWidget(QLabel(text))
        combo = QComboBox()
        combo.setMinimumWidth(130)
        combo.currentIndexChanged.connect(self.apply_filters)
        layout.addWidget(combo)
        return combo

    def make_table(self, headers, stretch=None):
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(30)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        if stretch is not None:
            table.horizontalHeader().setSectionResizeMode(stretch, QHeaderView.Stretch)
        return table

    def setup_overview_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 14, 12, 12)
        layout.setSpacing(12)
        grid = QGridLayout()
        grid.setSpacing(9)
        definitions = [
            ("sessions", "Sessions"), ("completed", "Completed"),
            ("messages", "Messages sent"), ("pii_messages", "Messages with PII"),
            ("pii_ignored", "PII sent after ignore"), ("ignored", "Warnings ignored"),
            ("misdetected", "Incorrect detections"), ("findings", "Raw sent findings"),
        ]
        self.metric_cards = {}
        for index, (key, title) in enumerate(definitions):
            card = MetricCard(title)
            self.metric_cards[key] = card
            grid.addWidget(card, index // 4, index % 4)
        layout.addLayout(grid)
        splitter = QSplitter(Qt.Vertical)
        self.figure = Figure(figsize=(10, 3), tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(210)
        splitter.addWidget(self.canvas)
        self.sessions_table = self.make_table([
            "Participant", "Condition", "Task", "Version", "Status", "Duration",
            "Messages", "Checked", "With PII", "PII after ignore", "Ignored",
            "Incorrect", "Warnings", "Hovers", "Rewrites",
        ], 2)
        self.sessions_table.cellDoubleClicked.connect(self.select_session_row)
        splitter.addWidget(self.sessions_table)
        splitter.setSizes([280, 380])
        layout.addWidget(splitter, 1)
        self.tabs.addTab(page, "Overview")

    def setup_messages_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 14, 12, 12)
        note = QLabel(
            "Each row links a sent message to raw detector output, participant corrections, "
            "ignored warnings, and the final classification. Message text is not logged."
        )
        note.setObjectName("infoText")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.messages_table = self.make_table([
            "Participant", "Condition", "Task", "Message", "Status", "Raw PII",
            "Raw findings", "Final PII", "Retained findings", "Ignored",
            "Incorrect", "Ignored classes", "Incorrect classes", "Outcome",
        ], 13)
        layout.addWidget(self.messages_table, 1)
        self.tabs.addTab(page, "Message outcomes")

    def setup_categories_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 14, 12, 12)
        splitter = QSplitter(Qt.Vertical)
        upper = QWidget()
        upper_layout = QVBoxLayout(upper)
        upper_layout.setContentsMargins(0, 0, 0, 0)
        upper_layout.addWidget(self.heading("Detections by class"))
        self.category_table = self.make_table([
            "Class", "Tier", "Draft detection episodes", "Raw sent findings",
            "Retained sent findings", "Ignored", "Incorrect", "Rewrites",
        ], 0)
        upper_layout.addWidget(self.category_table)
        splitter.addWidget(upper)
        lower = QWidget()
        lower_layout = QVBoxLayout(lower)
        lower_layout.setContentsMargins(0, 0, 0, 0)
        lower_layout.addWidget(self.heading("Warning decisions"))
        self.actions_table = self.make_table([
            "Participant", "Condition", "Task", "Message", "Draft", "Time",
            "Class", "Tier", "Selection",
        ], 6)
        lower_layout.addWidget(self.actions_table)
        splitter.addWidget(lower)
        splitter.setSizes([300, 360])
        layout.addWidget(splitter, 1)
        self.tabs.addTab(page, "Detections && Decisions")

    def setup_survey_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 14, 12, 12)
        self.survey_table = self.make_table([
            "Participant", "Condition", "Task", "Status", "Question", "Response",
        ], 5)
        self.survey_table.setWordWrap(True)
        self.survey_table.setTextElideMode(Qt.ElideNone)
        self.survey_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.survey_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.survey_table.horizontalHeader().sectionResized.connect(
            self.survey_table.resizeRowsToContents
        )
        layout.addWidget(self.survey_table)
        self.tabs.addTab(page, "Post-study survey")

    def setup_events_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 14, 12, 12)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Event type"))
        self.event_filter = QComboBox()
        self.event_filter.currentIndexChanged.connect(self.update_events)
        controls.addWidget(self.event_filter)
        controls.addWidget(QLabel("Search"))
        self.event_search = QLineEdit()
        self.event_search.setPlaceholderText("Search event metadata…")
        self.event_search.textChanged.connect(self.update_events)
        controls.addWidget(self.event_search, 1)
        layout.addLayout(controls)
        splitter = QSplitter(Qt.Vertical)
        self.events_table = self.make_table([
            "Participant", "Condition", "Task", "#", "Time", "Event", "Summary",
        ], 6)
        self.events_table.currentCellChanged.connect(self.show_event_details)
        splitter.addWidget(self.events_table)
        self.event_details = QPlainTextEdit()
        self.event_details.setReadOnly(True)
        self.event_details.setPlaceholderText("Select an event to inspect all logged metadata.")
        splitter.addWidget(self.event_details)
        splitter.setSizes([470, 190])
        layout.addWidget(splitter, 1)
        self.tabs.addTab(page, "Events")

    def setup_charts_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 14, 12, 12)
        layout.setSpacing(10)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Graph"))
        self.graph_selector = QComboBox()
        self.graph_selector.addItems([
            "PII outcomes by session",
            "Warning decisions by class",
            "Sent findings by class",
            "Interaction volume by session",
            "Event timeline",
        ])
        self.graph_selector.currentIndexChanged.connect(self.update_full_chart)
        self.graph_selector.setMinimumWidth(240)
        controls.addWidget(self.graph_selector)
        controls.addStretch()
        layout.addLayout(controls)
        self.graph_help = QLabel()
        self.graph_help.setObjectName("infoText")
        self.graph_help.setWordWrap(True)
        layout.addWidget(self.graph_help)
        self.chart_figure = Figure(figsize=(12, 6), tight_layout=True)
        self.chart_canvas = FigureCanvas(self.chart_figure)
        self.chart_toolbar = NavigationToolbar2QT(self.chart_canvas, self)
        self.chart_toolbar.setObjectName("chartToolbar")
        layout.addWidget(self.chart_toolbar)
        layout.addWidget(self.chart_canvas, 1)
        self.tabs.addTab(page, "Charts")

    def heading(self, text):
        label = QLabel(text)
        label.setObjectName("sectionTitle")
        return label

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Choose session folder", str(self.sessions_dir)
        )
        if folder:
            self.sessions_dir = Path(folder)
            self.subtitle.setText(str(self.sessions_dir))
            self.refresh_data()

    def refresh_data(self):
        combos = (
            self.task_filter, self.condition_filter,
            self.session_filter,
        )
        selected = [combo.currentData() for combo in combos]
        self.entries = []
        for folder in discover_sessions(self.sessions_dir):
            session = load_session(folder)
            record = analyze_session(session)
            if record.get("condition") in ("active", "silent"):
                self.entries.append({
                    "session": session, "record": record,
                    "details": session_analysis_details(session),
                })
        self.populate_filters(selected)
        self.apply_filters()

    def populate_filters(self, selected):
        combos = [self.task_filter, self.condition_filter, self.session_filter]
        for combo in combos:
            combo.blockSignals(True)
            combo.clear()
        self.task_filter.addItem("All tasks", None)
        for key, title in sorted({
            (e["record"].get("task_id"), e["record"].get("task_title")) for e in self.entries
        }):
            self.task_filter.addItem(title, key)
        self.condition_filter.addItem("All conditions", None)
        for value in ("active", "silent"):
            if any(e["record"].get("condition") == value for e in self.entries):
                self.condition_filter.addItem(value.title(), value)
        participants = {e["record"].get("participant_id") for e in self.entries} - {None}
        self.participant_filter.set_options(
            sorted(participants), self.participant_filter.selected_values()
        )
        self.session_filter.addItem("All sessions", None)
        for entry in self.entries:
            record = entry["record"]
            session_id = record.get("session_id")
            self.session_filter.addItem(
                f"{record.get('participant_id')} · {str(session_id)[:8]}", session_id
            )
        for combo, value in zip(combos, selected):
            index = combo.findData(value)
            combo.setCurrentIndex(index if index >= 0 else 0)
            combo.blockSignals(False)

    def apply_filters(self):
        task, condition, participant, session_id = (
            self.task_filter.currentData(), self.condition_filter.currentData(),
            self.participant_filter.selected_values(), self.session_filter.currentData(),
        )
        self.filtered_entries = [
            entry for entry in self.entries
            if (task is None or entry["record"].get("task_id") == task)
            and (condition is None or entry["record"].get("condition") == condition)
            and (not participant or entry["record"].get("participant_id") in participant)
            and (session_id is None or entry["record"].get("session_id") == session_id)
        ]
        self.filter_status.setText(f"{len(self.filtered_entries)} of {len(self.entries)} sessions")
        self.update_overview()
        self.update_messages()
        self.update_categories()
        self.update_surveys()
        self.rebuild_event_filter()
        self.update_full_chart()
        self.apply_sort()

    def refresh_sort_options(self, tab_index):
        options = {
            0: [
                ("Participant", "sessions", 0), ("Condition", "sessions", 1),
                ("Task", "sessions", 2), ("Duration", "sessions", 5),
                ("Messages", "sessions", 6), ("Messages with PII", "sessions", 8),
                ("Warnings ignored", "sessions", 10),
                ("Incorrect detections", "sessions", 11),
            ],
            1: [
                ("Participant", "messages", 0), ("Message number", "messages", 3),
                ("Raw PII", "messages", 5), ("Final PII", "messages", 7),
                ("Warnings ignored", "messages", 9),
                ("Incorrect detections", "messages", 10), ("Outcome", "messages", 13),
            ],
            2: [
                ("Class", "categories", 0), ("Tier", "categories", 1),
                ("Raw sent findings", "categories", 3),
                ("Retained sent findings", "categories", 4),
                ("Warnings ignored", "categories", 5),
                ("Incorrect detections", "categories", 6),
                ("Decision time", "actions", 5), ("Decision selection", "actions", 8),
            ],
            3: [
                ("Participant", "survey", 0), ("Condition", "survey", 1),
                ("Task", "survey", 2), ("Survey status", "survey", 3),
            ],
            4: [
                ("Event time", "events", 4), ("Event type", "events", 5),
                ("Participant", "events", 0), ("Task", "events", 2),
            ],
        }.get(tab_index, [])
        self.sort_filter.blockSignals(True)
        self.sort_filter.clear()
        for label, table, column in options:
            self.sort_filter.addItem(label, (table, column))
        self.sort_filter.blockSignals(False)
        self.sort_filter.setEnabled(bool(options))
        self.sort_order.setEnabled(bool(options))
        for widget in (
            self.sort_divider, self.sort_label, self.sort_filter, self.sort_order
        ):
            widget.setVisible(bool(options))
        self.apply_sort()

    def apply_sort(self):
        if not hasattr(self, "sort_filter"):
            return
        selection = self.sort_filter.currentData()
        if not selection:
            return
        tables = {
            "sessions": self.sessions_table, "messages": self.messages_table,
            "categories": self.category_table, "actions": self.actions_table,
            "survey": self.survey_table, "events": self.events_table,
        }
        table_name, column = selection
        table = tables[table_name]
        table.setSortingEnabled(True)
        table.sortItems(column, self.sort_order.currentData())
        table.setSortingEnabled(False)

    def update_overview(self):
        records = [entry["record"] for entry in self.filtered_entries]
        messages = [m for e in self.filtered_entries for m in e["details"]["messages"]]
        actions = [a for e in self.filtered_entries for a in e["details"]["warning_actions"]]
        values = {
            "sessions": len(records),
            "completed": sum(r.get("completed", False) for r in records),
            "messages": sum(r.get("messages_sent", 0) for r in records),
            "pii_messages": sum(bool(m.get("contains_pii")) for m in messages),
            "pii_ignored": sum(m.get("outcome") == "PII sent after ignore" for m in messages),
            "ignored": sum(a.get("reason") == "ignore" for a in actions),
            "misdetected": sum(a.get("reason") == "misdetected" for a in actions),
            "findings": sum(int(m.get("detector_finding_count") or 0) for m in messages),
        }
        for key, card in self.metric_cards.items():
            card.set_value(values[key])
        self.sessions_table.setRowCount(len(records))
        for row, record in enumerate(records):
            fields = [
                record.get("participant_id"), record.get("condition"), record.get("task_title"),
                record.get("task_version"), record.get("status"),
                f"{record['duration_seconds']:.1f}s" if record.get("duration_seconds") is not None else None,
                record.get("messages_sent"), record.get("messages_checked"),
                record.get("sensitive_messages_sent"), record.get("messages_pii_after_ignore"),
                record.get("warnings_ignored"), record.get("warnings_misdetected"),
                record.get("warning_exposures"), record.get("warning_hovers"),
                record.get("rewrites_accepted"),
            ]
            self.set_row(self.sessions_table, row, fields)
            self.sessions_table.item(row, 0).setData(Qt.UserRole, record.get("session_id"))
        self.update_chart(records)

    def select_session_row(self, row, _column):
        session_id = self.sessions_table.item(row, 0).data(Qt.UserRole)
        index = self.session_filter.findData(session_id)
        if index >= 0:
            self.session_filter.setCurrentIndex(index)

    def update_chart(self, records):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        colors = study_theme().colors
        self.figure.set_facecolor(colors["surface"])
        ax.set_facecolor(colors["surface"])
        ax.tick_params(colors=colors["body"], labelsize=9)
        ax.xaxis.label.set_color(colors["body"])
        ax.yaxis.label.set_color(colors["body"])
        ax.title.set_color(colors["heading"])
        for spine in ax.spines.values():
            spine.set_color(colors["border"])
        groups = defaultdict(list)
        for record in records:
            groups[record.get("condition", "unknown")].append(record)
        conditions = [name for name in ("active", "silent") if name in groups]
        metrics = [
            ("sensitive_message_rate", "PII message rate (%)", True, "#2563EB"),
            ("warnings_ignored", "Warnings ignored", False, "#B45309"),
            ("warnings_misdetected", "Incorrect detections", False, "#DC2626"),
            ("messages_pii_after_ignore", "PII after ignore", False, "#7E22CE"),
        ]
        if not conditions:
            ax.text(.5, .5, "No sessions match the filters", ha="center", va="center", transform=ax.transAxes)
        else:
            width = .8 / len(metrics)
            for metric_index, (field, label, percent, color) in enumerate(metrics):
                values = []
                for condition in conditions:
                    available = [r[field] for r in groups[condition] if r.get(field) is not None]
                    value = sum(available) / len(available) if available else 0
                    values.append(value * 100 if percent else value)
                positions = [i - .4 + width / 2 + metric_index * width for i in range(len(conditions))]
                ax.bar(positions, values, width, label=label, color=color)
            ax.set_xticks(range(len(conditions)), [name.title() for name in conditions])
            ax.set_ylabel("Mean per session")
            ax.legend(fontsize=8, ncols=2)
        ax.set_title("Condition comparison for current filters", fontsize=11)
        ax.grid(axis="y", alpha=.18)
        self.canvas.draw_idle()

    def prepare_chart(self, title, ylabel=""):
        self.chart_figure.clear()
        ax = self.chart_figure.add_subplot(111)
        colors = study_theme().colors
        self.chart_figure.set_facecolor(colors["surface"])
        ax.set_facecolor(colors["surface"])
        ax.set_title(title, color=colors["heading"], fontsize=13, pad=12)
        ax.set_ylabel(ylabel, color=colors["body"])
        ax.tick_params(colors=colors["body"], labelsize=9)
        for spine in ax.spines.values():
            spine.set_color(colors["border"])
        ax.grid(axis="y", color=colors["border"], alpha=.55, linewidth=.7)
        ax.set_axisbelow(True)
        return ax

    def update_full_chart(self):
        if not hasattr(self, "chart_figure"):
            return
        selected = self.graph_selector.currentText()
        descriptions = {
            "PII outcomes by session": (
                "Compares messages flagged by the raw detector, messages still classified as PII "
                "after participant corrections, and messages where retained PII was sent after Ignore anyway."
            ),
            "Warning decisions by class": (
                "Shows which warning classes participants chose to ignore and which they marked as incorrect detections."
            ),
            "Sent findings by class": (
                "Compares raw findings in sent messages with findings retained after participant corrections."
            ),
            "Interaction volume by session": (
                "Compares messages, warning episodes, completed warning hovers, and rewrite requests for each session."
            ),
            "Event timeline": (
                "Plots all recorded events by elapsed time. Each horizontal lane is one filtered session; colors match the Events tab."
            ),
        }
        self.graph_help.setText(descriptions.get(selected, ""))
        if selected == "PII outcomes by session":
            self.plot_pii_outcomes()
        elif selected == "Warning decisions by class":
            self.plot_warning_decisions()
        elif selected == "Sent findings by class":
            self.plot_sent_findings()
        elif selected == "Interaction volume by session":
            self.plot_interaction_volume()
        else:
            self.plot_event_timeline()
        self.chart_canvas.draw_idle()

    def session_chart_labels(self):
        labels = []
        for entry in self.filtered_entries:
            record = entry["record"]
            task = record.get("task_title", "Task")
            short_task = "Maya" if "Hardship" in task else (
                "Alex" if "Work Arrangement" in task else task[:16]
            )
            labels.append(f"{record.get('participant_id')}\n{short_task} · {record.get('condition', '').title()}")
        return labels

    def grouped_bars(self, ax, labels, series):
        if not labels:
            ax.text(.5, .5, "No sessions match the filters", ha="center", va="center",
                    transform=ax.transAxes)
            return
        width = .8 / max(len(series), 1)
        for series_index, (name, values, color) in enumerate(series):
            positions = [
                index - .4 + width / 2 + series_index * width
                for index in range(len(labels))
            ]
            bars = ax.bar(positions, values, width, label=name, color=color)
            for bar, value in zip(bars, values):
                if value:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2, bar.get_height(), str(value),
                        ha="center", va="bottom", fontsize=8, color=study_theme().colors["body"],
                    )
        ax.set_xticks(range(len(labels)), labels)
        ax.legend(fontsize=9, frameon=False, ncols=min(3, len(series)))

    def plot_pii_outcomes(self):
        ax = self.prepare_chart("PII outcomes by session", "Messages")
        labels = self.session_chart_labels()
        raw, final, ignored = [], [], []
        for entry in self.filtered_entries:
            messages = entry["details"]["messages"]
            raw.append(sum(bool(message.get("detector_contains_pii")) for message in messages))
            final.append(sum(bool(message.get("contains_pii")) for message in messages))
            ignored.append(sum(message.get("outcome") == "PII sent after ignore" for message in messages))
        self.grouped_bars(ax, labels, [
            ("Raw detector PII", raw, "#2563EB"),
            ("Final PII", final, "#7E22CE"),
            ("PII after ignore", ignored, "#FF8200"),
        ])

    def plot_warning_decisions(self):
        ax = self.prepare_chart("Warning decisions by class", "Decisions")
        totals = defaultdict(Counter)
        for entry in self.filtered_entries:
            for action in entry["details"]["warning_actions"]:
                totals[warning_category_title(action.get("category"))][action.get("reason")] += 1
        labels = sorted(totals, key=lambda label: sum(totals[label].values()), reverse=True)
        self.grouped_bars(ax, labels, [
            ("Ignore anyway", [totals[label]["ignore"] for label in labels], "#FF8200"),
            ("Incorrect detection", [totals[label]["misdetected"] for label in labels], "#DC2626"),
        ])
        ax.tick_params(axis="x", rotation=25)

    def plot_sent_findings(self):
        ax = self.prepare_chart("Sent-message findings by class", "Findings")
        raw, retained = Counter(), Counter()
        for entry in self.filtered_entries:
            for message in entry["details"]["messages"]:
                for item in message.get("detector_findings", []) or []:
                    raw[warning_category_title(item.get("category"))] += item.get("count", 1)
                for item in message.get("findings", []) or []:
                    retained[warning_category_title(item.get("category"))] += item.get("count", 1)
        labels = sorted(set(raw) | set(retained), key=lambda label: raw[label], reverse=True)
        self.grouped_bars(ax, labels, [
            ("Raw detector findings", [raw[label] for label in labels], "#2563EB"),
            ("Retained findings", [retained[label] for label in labels], "#7E22CE"),
        ])
        ax.tick_params(axis="x", rotation=25)

    def plot_interaction_volume(self):
        ax = self.prepare_chart("Interaction volume by session", "Recorded interactions")
        labels = self.session_chart_labels()
        records = [entry["record"] for entry in self.filtered_entries]
        self.grouped_bars(ax, labels, [
            ("Messages", [record.get("messages_sent", 0) for record in records], "#7E22CE"),
            ("Warning episodes", [record.get("warning_exposures") or 0 for record in records], "#FF8200"),
            ("Warning hovers", [record.get("warning_hovers") or 0 for record in records], "#2563EB"),
            ("Rewrite requests", [record.get("rewrites_requested") or 0 for record in records], "#047857"),
        ])

    def plot_event_timeline(self):
        ax = self.prepare_chart("Study event timeline", "Session")
        labels = self.session_chart_labels()
        present_groups = set()
        for lane, entry in enumerate(self.filtered_entries):
            grouped = defaultdict(list)
            for event in entry["details"]["events"]:
                group = event_group(event.get("event_type"))
                grouped[group].append(event.get("elapsed_ms", 0) / 1000)
                present_groups.add(group)
            for group, times in grouped.items():
                ax.scatter(times, [lane] * len(times), s=28, alpha=.8,
                           color=EVENT_COLORS[group], label=group)
        ax.set_yticks(range(len(labels)), labels)
        ax.set_xlabel("Elapsed time (seconds)", color=study_theme().colors["body"])
        ax.grid(axis="x", color=study_theme().colors["border"], alpha=.55)
        handles = [
            ax.scatter([], [], s=30, color=EVENT_COLORS[group], label=group)
            for group in EVENT_COLORS if group in present_groups
        ]
        if handles:
            ax.legend(handles=handles, fontsize=9, frameon=False, ncols=min(4, len(handles)))
        if not labels:
            ax.text(.5, .5, "No sessions match the filters", ha="center", va="center",
                    transform=ax.transAxes)

    def update_messages(self):
        rows = []
        for entry in self.filtered_entries:
            record = entry["record"]
            for message in entry["details"]["messages"]:
                rows.append([
                    record.get("participant_id"), record.get("condition"), record.get("task_title"),
                    message.get("message_id"), message.get("detection_status", "unchecked"),
                    message.get("detector_contains_pii"), breakdown_text(message.get("detector_findings")),
                    message.get("contains_pii"), breakdown_text(message.get("findings")),
                    message.get("ignored_count", 0), message.get("misdetected_count", 0),
                    ", ".join(warning_category_title(c) for c in message.get("ignored_categories", [])) or "—",
                    ", ".join(warning_category_title(c) for c in message.get("misdetected_categories", [])) or "—",
                    message.get("outcome"),
                ])
        self.messages_table.setRowCount(len(rows))
        for row, fields in enumerate(rows):
            self.set_row(self.messages_table, row, fields)
            outcome = fields[-1]
            color = "#B45309" if outcome == "PII sent after ignore" else (
                "#DC2626" if outcome == "PII detected" else "#047857"
            )
            self.messages_table.item(row, len(fields) - 1).setForeground(QColor(color))
        for column, width in {2: 230, 6: 330, 8: 280, 11: 190, 12: 190, 13: 210}.items():
            self.messages_table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.Interactive
            )
            self.messages_table.setColumnWidth(column, width)

    def update_categories(self):
        totals = defaultdict(Counter)
        actions = []
        for entry in self.filtered_entries:
            record = entry["record"]
            for stat in entry["details"]["category_stats"]:
                key = (stat.get("category"), stat.get("tier"))
                for field, value in stat.items():
                    if field not in ("category", "tier"):
                        totals[key][field] += value
            for action in entry["details"]["warning_actions"]:
                actions.append([
                    record.get("participant_id"), record.get("condition"), record.get("task_title"),
                    action.get("message_id"), action.get("draft_id"),
                    f"{action.get('elapsed_ms', 0) / 1000:.1f}s",
                    warning_category_title(action.get("category")), action.get("tier"),
                    "Ignore anyway" if action.get("reason") == "ignore" else "Incorrect detection",
                ])
        self.category_table.setRowCount(len(totals))
        ordered = sorted(totals.items(), key=lambda item: (item[0][0], item[0][1] or 0))
        for row, ((category, tier), counts) in enumerate(ordered):
            self.set_row(self.category_table, row, [
                warning_category_title(category), tier, counts["draft_detection_episodes"],
                counts["sent_raw_findings"], counts["sent_retained_findings"],
                counts["ignored"], counts["misdetected"], counts["rewrites"],
            ])
        self.actions_table.setRowCount(len(actions))
        for row, fields in enumerate(actions):
            self.set_row(self.actions_table, row, fields)
            self.actions_table.item(row, 8).setForeground(QColor(
                "#B45309" if fields[8] == "Ignore anyway" else "#DC2626"
            ))

    def update_surveys(self):
        rows = []
        for entry in self.filtered_entries:
            record = entry["record"]
            responses = record.get("survey_responses", [])
            if responses:
                for response in responses:
                    rows.append([
                        record.get("participant_id"), record.get("condition"), record.get("task_title"),
                        record.get("survey_status"), response.get("question"),
                        response.get("response_text") or "[No response]",
                    ])
            else:
                rows.append([
                    record.get("participant_id"), record.get("condition"), record.get("task_title"),
                    record.get("survey_status"), "—", "—",
                ])
        self.survey_table.setRowCount(len(rows))
        for row, fields in enumerate(rows):
            self.set_row(self.survey_table, row, fields)

    def rebuild_event_filter(self):
        selected = self.event_filter.currentData()
        event_types = sorted({
            event.get("event_type", "unknown") for entry in self.filtered_entries
            for event in entry["details"]["events"]
        })
        self.event_filter.blockSignals(True)
        self.event_filter.clear()
        self.event_filter.addItem("All events", None)
        for event_type in event_types:
            self.event_filter.addItem(event_type, event_type)
        index = self.event_filter.findData(selected)
        self.event_filter.setCurrentIndex(index if index >= 0 else 0)
        self.event_filter.blockSignals(False)
        self.update_events()

    def update_events(self):
        selected = self.event_filter.currentData()
        search = self.event_search.text().strip().lower()
        rows = []
        self.filtered_events = []
        for entry in self.filtered_entries:
            record = entry["record"]
            for event in entry["details"]["events"]:
                if selected and event.get("event_type") != selected:
                    continue
                if search and search not in json.dumps(event, ensure_ascii=False, default=str).lower():
                    continue
                self.filtered_events.append((record, event))
                summary = "  |  ".join(
                    f"{key}: {json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value}"
                    for key, value in event.get("details", {}).items()
                )
                rows.append([
                    record.get("participant_id"), record.get("condition"), record.get("task_title"),
                    event.get("event_id"), f"{event.get('elapsed_ms', 0) / 1000:.3f}s",
                    event.get("event_type"), summary,
                ])
        self.events_table.setRowCount(len(rows))
        for row, fields in enumerate(rows):
            self.set_row(self.events_table, row, fields)
            self.events_table.item(row, 0).setData(
                Qt.UserRole + 1, self.filtered_events[row]
            )
            self.events_table.item(row, 5).setForeground(
                QColor(EVENT_COLORS[event_group(fields[5])])
            )
        self.event_details.clear()
        if self.tabs.currentIndex() == 4:
            self.apply_sort()

    def show_event_details(self, row, _column, _old_row, _old_column):
        if row >= 0 and self.events_table.item(row, 0) is not None:
            payload_data = self.events_table.item(row, 0).data(Qt.UserRole + 1)
            if not payload_data:
                return
            record, event = payload_data
            payload = {
                "participant_id": record.get("participant_id"),
                "task": record.get("task_title"), **event,
            }
            self.event_details.setPlainText(json.dumps(payload, indent=2, ensure_ascii=False))

    def set_row(self, table, row, fields):
        for column, value in enumerate(fields):
            item = SortableItem(display(value))
            if isinstance(value, str) and value.endswith("s"):
                try:
                    sort_value = float(value[:-1])
                except ValueError:
                    sort_value = value.lower()
            elif isinstance(value, str):
                sort_value = value.lower()
            else:
                sort_value = value
            item.setData(Qt.UserRole, sort_value)
            item.setToolTip(display(value, ""))
            table.setItem(row, column, item)

    def export_filtered_data(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Export filtered study data", str(self.sessions_dir)
        )
        if not folder:
            return
        target = Path(folder)
        records = [entry["record"] for entry in self.filtered_entries]
        messages = []
        actions = []
        categories = defaultdict(Counter)
        surveys = []
        events = []
        for entry in self.filtered_entries:
            record = entry["record"]
            base = {
                "participant_id": record.get("participant_id"),
                "condition": record.get("condition"),
                "task_id": record.get("task_id"),
                "task_title": record.get("task_title"),
                "session_id": record.get("session_id"),
            }
            for message in entry["details"]["messages"]:
                messages.append({**base, **{
                    key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
                    for key, value in message.items()
                }})
            for action in entry["details"]["warning_actions"]:
                actions.append({**base, **action})
            for stat in entry["details"]["category_stats"]:
                key = (stat.get("category"), stat.get("tier"))
                for field, value in stat.items():
                    if field not in ("category", "tier"):
                        categories[key][field] += value
            for response in record.get("survey_responses", []):
                surveys.append({
                    **base, "survey_status": record.get("survey_status"),
                    "question_id": response.get("question_id"),
                    "question": response.get("question"),
                    "response": response.get("response_text"),
                })
            for event in entry["details"]["events"]:
                events.append({**base, **event})
        category_rows = [
            {"category": category, "tier": tier, **counts}
            for (category, tier), counts in sorted(
                categories.items(), key=lambda item: (item[0][0], item[0][1] or 0)
            )
        ]
        session_rows = [{
            key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
            for key, value in record.items() if key != "folder"
        } for record in records]
        for name, rows in (
            ("sessions.csv", session_rows), ("messages.csv", messages),
            ("warning_decisions.csv", actions), ("detection_classes.csv", category_rows),
            ("survey_responses.csv", surveys),
        ):
            self.write_csv(target / name, rows)
        with (target / "events.jsonl").open("w", encoding="utf-8") as file:
            for event in events:
                file.write(json.dumps(event, ensure_ascii=False) + "\n")
        self.filter_status.setText(
            f"Exported {len(self.filtered_entries)} sessions to {target}"
        )

    @staticmethod
    def write_csv(path, rows):
        if not rows:
            path.write_text("", encoding="utf-8")
            return
        fields = []
        for row in rows:
            for key in row:
                if key not in fields:
                    fields.append(key)
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

    def apply_styles(self):
        self.setStyleSheet(study_theme().stylesheet("""
            QMainWindow { background: $page; }
            QWidget { color: $text; }
            QWidget#qt_tabwidget_stackedwidget, QTabWidget QWidget { background: $surface; }
            QLabel#pageTitle { color: $heading; font-size: 24px; font-weight: 700; }
            QLabel#sectionTitle { color: $heading; font-size: 16px; font-weight: 650; }
            QLabel#mutedText { color: $muted; font-size: 12px; }
            QLabel#infoText { color: $body; background: $subtle; border: 1px solid $border;
                border-radius: 7px; padding: 10px 12px; }
            QFrame#filterBar { background: $surface; border: 1px solid $border; border-radius: 9px; }
            QFrame#filterBar QLabel { background: transparent; border: none; color: $secondary; }
            QFrame#filterDivider { color: $border; background: $border; max-width: 1px; border: none; }
            QFrame#metricCard { background: $surface; border: 1px solid $border;
                border-left: 3px solid $primary; border-radius: 8px; }
            QFrame#metricCard QLabel { background: transparent; border: none; }
            QLabel#metricTitle { color: $muted; font-size: 11px; font-weight: 500; }
            QLabel#metricValue { color: $heading; font-size: 22px; font-weight: 700; }
            QPushButton { background: $subtle; color: $text; border: 1px solid $control_border;
                border-radius: 7px; padding: 7px 14px; min-height: 18px; }
            QPushButton:hover { background: $hover; border-color: $strong_border; }
            QPushButton:focus { border: 2px solid $primary; padding: 6px 13px; }
            QPushButton#primaryButton { background: $primary; color: $on_primary;
                border: 1px solid $primary; font-weight: 650; }
            QPushButton#primaryButton:hover { background: $primary_hover; }
            QComboBox, QLineEdit { background: $surface; color: $text; border: 1px solid $control_border;
                border-radius: 6px; padding: 6px 9px; min-height: 19px; }
            QComboBox:hover, QLineEdit:hover { border-color: $strong_border; }
            QComboBox:focus, QLineEdit:focus { border: 2px solid $primary; padding: 5px 8px; }
            QComboBox::drop-down { border: none; width: 24px; }
            QTabWidget::pane { background: $surface; border: 1px solid $border;
                border-radius: 8px; top: -1px; }
            QTabBar { background: transparent; }
            QTabBar::tab { background: transparent; color: $muted; padding: 10px 15px;
                margin-right: 2px; border: 1px solid transparent; border-bottom: 3px solid transparent; }
            QTabBar::tab:hover { color: $heading; background: $subtle; border-top-left-radius: 6px;
                border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: $surface; color: $heading; font-weight: 650;
                border: 1px solid $border; border-bottom: 3px solid $primary;
                border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTableWidget { background: $surface; alternate-background-color: $editor; color: $text;
                border: 1px solid $border; border-radius: 6px; gridline-color: $border;
                selection-background-color: $selection; selection-color: $heading; outline: none; }
            QTableWidget::item { padding: 6px; border: none; }
            QTableWidget::item:hover { background: $hover; }
            QHeaderView { background: $subtle; }
            QHeaderView::section { background: $subtle; color: $heading; border: none;
                border-right: 1px solid $border; border-bottom: 1px solid $border;
                padding: 8px 7px; font-weight: 650; }
            QTableCornerButton::section { background: $subtle; border: none;
                border-right: 1px solid $border; border-bottom: 1px solid $border; }
            QPlainTextEdit { background: $editor; color: $text; border: 1px solid $border;
                border-radius: 7px; padding: 10px; font-family: Consolas; font-size: 12px; }
            QPlainTextEdit:focus { border: 1px solid $primary; }
            QToolBar#chartToolbar { background: $surface; border: 1px solid $border;
                border-radius: 6px; spacing: 4px; padding: 3px; }
            QToolBar#chartToolbar QToolButton { background: transparent; border: 1px solid transparent;
                border-radius: 4px; padding: 4px; }
            QToolBar#chartToolbar QToolButton:hover { background: $hover; border-color: $border; }
            QSplitter::handle { background: transparent; margin: 3px; }
            QSplitter::handle:hover { background: $hover; border-radius: 2px; }
            FigureCanvas { background: $surface; border: 1px solid $border; border-radius: 7px; }
        """))
        if self.filtered_entries:
            self.update_chart([entry["record"] for entry in self.filtered_entries])
            self.update_full_chart()
