import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QListWidget,
    QComboBox,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QPlainTextEdit,
    QSplitter,
    QFrame,
    QHeaderView,
    QFileDialog,
    QMessageBox,
)

from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT,
)
from matplotlib.backend_bases import MouseButton
from matplotlib.figure import Figure

from analytics.session_data import (
    DEFAULT_SESSIONS_DIR,
    discover_sessions,
    load_session,
    summarize_session,
    available_event_types,
    filter_events,
)


EVENT_COLORS = {
    "Session": "#475569",
    "Detection": "#2563EB",
    "Warning": "#B45309",
    "Message": "#7E22CE",
    "Document": "#047857",
    "Other": "#64748B",
}


def event_group(event_type):
    return {
        "session": "Session", "consent": "Session",
        "task": "Session", "profile": "Session",
        "detection": "Detection", "warning": "Warning",
        "message": "Message", "document": "Document",
    }.get(event_type.partition("_")[0], "Other")


class MetricCard(QFrame):
    def __init__(self, title):
        super().__init__()

        self.setObjectName("metricCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(3)

        heading = QLabel(title)
        heading.setObjectName("metricTitle")

        self.value_label = QLabel("—")
        self.value_label.setObjectName("metricValue")

        layout.addWidget(heading)
        layout.addWidget(self.value_label)

    def set_value(self, value):
        self.value_label.setText(str(value))


class SessionResultsWindow(QMainWindow):
    def __init__(self, sessions_dir=DEFAULT_SESSIONS_DIR):
        super().__init__()

        self.sessions_dir = Path(sessions_dir)
        self.current_session = None
        self.filtered_events = []
        self.timeline_rows = {}

        self.setWindowTitle(
            "PromptShield — Session Inspector"
        )
        self.setup_ui()
        available = self.screen().availableGeometry()
        self.resize(min(1700, available.width() - 32),
                    min(1050, available.height() - 64))
        self.apply_styles()
        self.refresh_sessions()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        main_splitter = QSplitter(Qt.Horizontal)
        root.addWidget(main_splitter)

        # -------------------------------------------------
        # Left panel: session browser
        # -------------------------------------------------

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(230)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 16, 16, 16)
        sidebar_layout.setSpacing(12)

        sidebar_title = QLabel("Study Sessions")
        sidebar_title.setObjectName("sectionTitle")

        sidebar_layout.addWidget(sidebar_title)

        self.folder_label = QLabel(
            str(self.sessions_dir)
        )
        self.folder_label.setObjectName("hintLabel")
        self.folder_label.setWordWrap(True)

        sidebar_layout.addWidget(self.folder_label)

        browse_button = QPushButton("Choose Folder")
        browse_button.clicked.connect(
            self.choose_sessions_folder
        )

        refresh_button = QPushButton("Refresh Sessions")
        refresh_button.clicked.connect(
            self.refresh_sessions
        )

        sidebar_layout.addWidget(browse_button)
        sidebar_layout.addWidget(refresh_button)

        self.session_list = QListWidget()
        self.session_list.currentRowChanged.connect(
            self.load_selected_session
        )

        sidebar_layout.addWidget(
            self.session_list, 1
        )

        main_splitter.addWidget(sidebar)

        # -------------------------------------------------
        # Right panel
        # -------------------------------------------------

        content = QWidget()

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(14)

        header = QHBoxLayout()

        self.session_title = QLabel(
            "Select a session"
        )
        self.session_title.setObjectName(
            "pageTitle"
        )

        self.session_subtitle = QLabel("")
        self.session_subtitle.setObjectName(
            "hintLabel"
        )
        self.session_subtitle.setWordWrap(True)

        title_layout = QVBoxLayout()
        title_layout.addWidget(
            self.session_title
        )
        title_layout.addWidget(
            self.session_subtitle
        )

        header.addLayout(title_layout, 1)

        content_layout.addLayout(header)

        # -------------------------------------------------
        # Summary cards
        # -------------------------------------------------

        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(10)

        metric_definitions = [
            ("duration", "Session Duration"),
            ("total_events", "Total Events"),
            ("detection_checks", "Detection Checks"),
            ("positive_checks", "Positive Checks"),
            ("warning_hovers", "Warning Hovers"),
            ("messages_sent", "Messages Sent"),
            ("documents_submitted", "Documents Submitted"),
        ]

        self.metric_cards = {}

        for index, (key, label) in enumerate(
            metric_definitions
        ):
            card = MetricCard(label)

            self.metric_cards[key] = card

            metrics_layout.addWidget(
                card,
                index // 4,
                index % 4
            )

        content_layout.addLayout(
            metrics_layout
        )

        # -------------------------------------------------
        # Chart controls
        # -------------------------------------------------

        workspace = QSplitter(Qt.Vertical)
        content_layout.addWidget(workspace, 1)

        chart_panel = QWidget()
        chart_layout = QVBoxLayout(chart_panel)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        chart_controls = QHBoxLayout()

        chart_title = QLabel("Visualization")
        chart_title.setObjectName("sectionTitle")

        self.chart_combo = QComboBox()
        self.chart_combo.addItems([
            "Event Timeline",
            "Event Counts",
            "Detection Timeline",
        ])

        self.chart_combo.currentIndexChanged.connect(
            self.update_chart
        )

        chart_controls.addWidget(
            chart_title
        )
        chart_controls.addStretch()
        chart_controls.addWidget(
            self.chart_combo
        )

        chart_layout.addLayout(chart_controls)

        self.figure = Figure(
            figsize=(8, 3),
            tight_layout=True
        )

        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(155)
        self.canvas.mpl_connect("pick_event", self.select_timeline_event)
        chart_layout.addWidget(self.canvas, 1)
        self.chart_toolbar = NavigationToolbar2QT(self.canvas, chart_panel)
        chart_layout.addWidget(self.chart_toolbar)
        workspace.addWidget(chart_panel)

        # -------------------------------------------------
        # Event filters
        # -------------------------------------------------

        explorer = QWidget()
        explorer_layout = QVBoxLayout(explorer)
        explorer_layout.setContentsMargins(0, 0, 0, 0)
        filters = QHBoxLayout()

        events_title = QLabel("Event Explorer")
        events_title.setObjectName("sectionTitle")

        self.event_filter = QComboBox()
        self.event_filter.addItem("All events")
        self.event_filter.currentIndexChanged.connect(
            self.refresh_event_table
        )

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search event names or metadata..."
        )
        self.search_input.textChanged.connect(
            self.refresh_event_table
        )

        filters.addWidget(events_title)
        filters.addStretch()
        filters.addWidget(self.event_filter)
        filters.addWidget(self.search_input)

        explorer_layout.addLayout(filters)

        # -------------------------------------------------
        # Event table and JSON inspector
        # -------------------------------------------------

        lower_splitter = QSplitter(Qt.Horizontal)

        self.event_table = QTableWidget()
        self.event_table.setColumnCount(4)
        self.event_table.setHorizontalHeaderLabels([
            "Event #",
            "Elapsed",
            "Event Type",
            "Summary",
        ])
        self.event_table.verticalHeader().hide()
        self.event_table.setWordWrap(False)

        self.event_table.setSelectionBehavior(
            QTableWidget.SelectRows
        )
        self.event_table.setSelectionMode(
            QTableWidget.SingleSelection
        )
        self.event_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.event_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.event_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        self.event_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )
        self.event_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.Stretch
        )

        self.event_table.itemSelectionChanged.connect(
            self.show_event_details
        )

        lower_splitter.addWidget(
            self.event_table
        )

        self.details_view = QPlainTextEdit()
        self.details_view.setReadOnly(True)
        self.details_view.setPlaceholderText(
            "Select an event to inspect its metadata."
        )

        lower_splitter.addWidget(
            self.details_view
        )

        lower_splitter.setSizes([900, 420])
        lower_splitter.setStretchFactor(0, 3)
        lower_splitter.setStretchFactor(1, 1)
        explorer_layout.addWidget(lower_splitter, 1)
        workspace.addWidget(explorer)
        workspace.setSizes([300, 410])

        main_splitter.addWidget(content)
        main_splitter.setSizes([280, 1170])

        self.statusBar().showMessage(
            "Read-only session inspector"
        )

    # -----------------------------------------------------
    # Session loading
    # -----------------------------------------------------

    def choose_sessions_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Study Sessions Folder",
            str(self.sessions_dir)
        )

        if folder:
            self.sessions_dir = Path(folder)
            self.refresh_sessions()

    def refresh_sessions(self):
        self.session_folders = discover_sessions(
            self.sessions_dir
        )

        self.folder_label.setText(
            str(self.sessions_dir)
        )

        self.session_list.blockSignals(True)
        self.session_list.clear()

        for folder in self.session_folders:
            self.session_list.addItem(
                folder.name
            )

        self.session_list.blockSignals(False)

        if self.session_folders:
            self.session_list.setCurrentRow(0)
        else:
            self.current_session = None
            self.clear_display()

    def load_selected_session(self, index):
        if index < 0 or index >= len(
            self.session_folders
        ):
            return

        folder = self.session_folders[index]

        self.current_session = load_session(
            folder
        )

        session = self.current_session
        metadata = session["metadata"]

        participant = metadata.get(
            "participant_id", folder.name
        )

        condition = metadata.get(
            "condition", "Unknown"
        )

        status = metadata.get(
            "status", "Unknown"
        )

        self.session_title.setText(
            f"Participant {participant}"
        )

        self.session_subtitle.setText(
            f"Condition: {condition}   |   "
            f"Status: {status}   |   "
            f"Session: {metadata.get('session_id', 'Unknown')}"
        )

        if session["errors"]:
            self.statusBar().showMessage(
                f"{len(session['errors'])} file-reading "
                "warning(s) — inspect source files"
            )
        else:
            self.statusBar().showMessage(
                f"Loaded {len(session['events'])} events"
            )

        self.update_metrics()

        # Automatically discover event types.
        self.event_filter.blockSignals(True)
        self.event_filter.clear()
        self.event_filter.addItem("All events")

        self.event_filter.addItems(
            available_event_types(
                session["events"]
            )
        )

        self.event_filter.blockSignals(False)
        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)

        self.refresh_event_table()
        if self.chart_combo.currentText() != "Event Timeline":
            self.update_chart()

    def clear_display(self):
        self.session_title.setText(
            "No sessions found"
        )
        self.session_subtitle.setText(
            "Choose a folder containing study sessions."
        )

        for card in self.metric_cards.values():
            card.set_value("—")

        self.filtered_events = []
        self.timeline_rows.clear()
        self.event_table.setRowCount(0)
        self.details_view.clear()

        self.figure.clear()
        self.canvas.draw_idle()

    # -----------------------------------------------------
    # Summary metrics
    # -----------------------------------------------------

    def update_metrics(self):
        if self.current_session is None:
            return

        summary = summarize_session(
            self.current_session
        )

        for key, card in self.metric_cards.items():
            value = summary.get(key)
            card.set_value("—" if value is None else value)

    # -----------------------------------------------------
    # Event table
    # -----------------------------------------------------

    def refresh_event_table(self):
        if self.current_session is None:
            return

        event_type = (
            self.event_filter.currentText()
        )

        search = (
            self.search_input.text().strip()
        )

        self.filtered_events = filter_events(
            self.current_session["events"],
            event_type=event_type,
            search=search
        )

        table = self.event_table
        table.setCurrentCell(-1, -1)
        table.setRowCount(
            len(self.filtered_events)
        )

        for row, event in enumerate(
            self.filtered_events
        ):
            details = event.get("details", {})

            elapsed = (
                event.get("elapsed_ms", 0) / 1000
            )

            fields = [
                str(event.get("event_id", "")),
                f"{elapsed:.3f}s",
                event.get("event_type", ""),
                self.format_event_summary(details),
            ]

            for column, value in enumerate(fields):
                item = QTableWidgetItem(value)
                if column == 2:
                    item.setForeground(QColor(EVENT_COLORS[event_group(value)]))
                table.setItem(
                    row, column, item
                )

        self.details_view.clear()
        if self.chart_combo.currentText() == "Event Timeline":
            self.update_chart()

    def format_event_summary(self, details):
        """Generic summary for any future event type."""

        if not isinstance(details, dict):
            return str(details)

        parts = []

        for key, value in details.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(
                    value,
                    ensure_ascii=False
                )

            parts.append(
                f"{key}: {value}"
            )

        summary = "  |  ".join(parts)

        return (
            summary[:300] + "..."
            if len(summary) > 300
            else summary
        )

    def show_event_details(self):
        row = self.event_table.currentRow()

        if row < 0 or row >= len(
            self.filtered_events
        ):
            return

        event = self.filtered_events[row]

        self.details_view.setPlainText(
            json.dumps(
                event,
                indent=2,
                ensure_ascii=False
            )
        )

    # -----------------------------------------------------
    # Charts
    # -----------------------------------------------------

    def update_chart(self):
        if self.current_session is None:
            return

        self.timeline_rows.clear()
        self.chart_toolbar.update()
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        selected = self.chart_combo.currentText()

        if selected == "Event Timeline":
            self.plot_event_timeline(ax)
        elif selected == "Detection Timeline":
            self.plot_detection_timeline(ax)
        else:
            self.plot_event_counts(ax)

        ax.grid(
            axis="y",
            alpha=0.18
        )

        self.canvas.draw_idle()

    def plot_event_timeline(self, ax):
        groups = {}
        for row, event in enumerate(self.filtered_events):
            group = event_group(event.get("event_type") or "unknown")
            groups.setdefault(group, []).append(row)

        lanes = [group for group in EVENT_COLORS if group in groups]
        for lane, group in enumerate(lanes):
            rows = groups[group]
            times = [self.filtered_events[row].get("elapsed_ms", 0) / 1000
                     for row in rows]
            points = ax.scatter(times, [lane] * len(rows),
                                color=EVENT_COLORS[group], s=40, picker=5)
            self.timeline_rows[points] = rows

        ax.set_yticks(range(len(lanes)), lanes)
        ax.set_ylim(max(len(lanes), 1) - 0.5, -0.5)
        ax.set_xlabel("Elapsed time (seconds)")
        ax.set_title("Click an event to inspect its metadata" if lanes
                     else "No events match the current filters", fontsize=10)

    def select_timeline_event(self, event):
        rows = self.timeline_rows.get(event.artist)
        time = event.mouseevent.xdata
        if (rows is None or not len(event.ind) or time is None
                or event.mouseevent.button != MouseButton.LEFT or self.chart_toolbar.mode):
            return

        offsets = event.artist.get_offsets()
        nearest = min(event.ind, key=lambda index: abs(offsets[index, 0] - time))
        overlapping_rows = [rows[index] for index in event.ind
                            if offsets[index, 0] == offsets[nearest, 0]]
        row = rows[nearest]
        current = self.event_table.currentRow()
        if current in overlapping_rows:
            row = overlapping_rows[(overlapping_rows.index(current) + 1) % len(overlapping_rows)]
        self.event_table.setCurrentCell(row, 2)
        self.event_table.scrollToItem(self.event_table.item(row, 2))

    def plot_event_counts(self, ax):
        summary = summarize_session(
            self.current_session
        )

        counts = summary["event_counts"]

        if not counts:
            ax.text(
                0.5, 0.5,
                "No events recorded",
                ha="center",
                va="center",
                transform=ax.transAxes
            )
            return

        names = [
            name
            for name, _ in counts.most_common()
        ]

        values = [
            counts[name]
            for name in names
        ]

        ax.bar(
            range(len(names)),
            values
        )

        ax.set_xticks(
            range(len(names))
        )

        ax.set_xticklabels(
            names,
            rotation=35,
            ha="right",
            fontsize=8
        )

        ax.set_ylabel("Event count")
        ax.set_title("Recorded Events by Type")

    def plot_detection_timeline(self, ax):
        events = self.current_session["events"]

        detections = [
            event for event in events
            if event.get("event_type")
            == "detection_completed"
        ]

        if not detections:
            ax.text(
                0.5, 0.5,
                "No detection events recorded",
                ha="center",
                va="center",
                transform=ax.transAxes
            )
            return

        times = [
            event.get("elapsed_ms", 0) / 1000
            for event in detections
        ]

        findings = [
            event.get("details", {}).get(
                "finding_count", 0
            )
            for event in detections
        ]

        ax.plot(
            times,
            findings,
            marker="o",
            linewidth=1.5
        )

        # Mark actions without confusing them with
        # detection findings.
        markers = {
            "message_sent": "Message sent",
            "document_submitted": "Document submitted",
        }

        shown = set()

        for event in events:
            event_type = event.get("event_type")

            if event_type not in markers:
                continue

            elapsed = (
                event.get("elapsed_ms", 0) / 1000
            )

            label = markers[event_type]

            if label in shown:
                label = None
            else:
                shown.add(label)

            ax.axvline(
                elapsed,
                linestyle="--",
                alpha=0.5,
                label=label
            )

        if shown:
            ax.legend(fontsize=8)

        ax.set_xlabel("Elapsed time (seconds)")
        ax.set_ylabel("Findings per check")
        ax.set_title("PromptShield Detection Timeline")
        ax.set_ylim(bottom=-0.1)

    # -----------------------------------------------------
    # Styling
    # -----------------------------------------------------

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F8FAFC;
            }

            QWidget {
                color: #1E293B;
                font-size: 13px;
            }

            QFrame#sidebar {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
            }

            QFrame#metricCard {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 9px;
            }

            QLabel#pageTitle {
                font-size: 22px;
                font-weight: bold;
                color: #0F172A;
            }

            QLabel#sectionTitle {
                font-size: 15px;
                font-weight: bold;
                color: #0F172A;
            }

            QLabel#metricTitle {
                color: #64748B;
                font-size: 11px;
            }

            QLabel#metricValue {
                color: #0F172A;
                font-size: 23px;
                font-weight: bold;
            }

            QLabel#hintLabel {
                color: #64748B;
                font-size: 11px;
            }

            QPushButton {
                padding: 9px 12px;
                background-color: #2563EB;
                color: white;
                border: none;
                border-radius: 7px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #1D4ED8;
            }

            QListWidget,
            QTableWidget,
            QPlainTextEdit,
            QLineEdit,
            QComboBox {
                background-color: white;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 5px;
            }

            QListWidget::item:selected {
                background-color: #DBEAFE;
                color: #1D4ED8;
            }

            QTableWidget::item:selected {
                background-color: #DBEAFE;
                color: #1E293B;
            }
        """)
