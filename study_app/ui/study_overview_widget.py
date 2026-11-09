
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSplitter,
)

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg as FigureCanvas
)

from analytics.study_analysis import (
    load_study,
    summarize_study,
)


class StudyOverviewWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "PromptShield — Study Overview"
        )
        self.resize(1200, 800)

        self.records = []
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()

        title = QLabel("Study Overview")
        title.setStyleSheet(
            "font-size: 23px; font-weight: bold;"
        )

        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh_data)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(refresh)

        layout.addLayout(header)

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        controls = QHBoxLayout()

        controls.addWidget(QLabel("Visualization:"))

        self.chart_selector = QComboBox()
        self.chart_selector.addItems([
            "Completion Time",
            "Messages Sent",
            "Detection Checks",
            "Positive Detection Checks",
            "Warning Exposures",
            "Warning Hovers",
        ])
        self.chart_selector.currentIndexChanged.connect(
            self.update_chart
        )

        controls.addWidget(self.chart_selector)
        controls.addStretch()
        layout.addLayout(controls)

        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter, 1)

        self.figure = Figure(
            figsize=(8, 3),
            tight_layout=True
        )
        self.canvas = FigureCanvas(self.figure)
        splitter.addWidget(self.canvas)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Participant",
            "Condition",
            "Status",
            "Duration (s)",
            "Messages",
            "Checks",
            "Positive Checks",
            "Warnings",
        ])

        self.table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )
        self.table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setStretchLastSection(
            True
        )

        splitter.addWidget(self.table)
        splitter.setSizes([350, 300])

        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #F8FAFC;
                color: #1E293B;
            }

            QTableWidget, QComboBox {
                background-color: white;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 5px;
            }

            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                padding: 9px 15px;
                border-radius: 7px;
            }

            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)

    def refresh_data(self):
        self.records = load_study()

        summary = summarize_study(self.records)

        active = summary["active"]
        silent = summary["silent"]

        def mean_text(group, metric):
            value = group[metric]["mean"]
            return (
                f"{value:.1f}"
                if value is not None
                else "N/A"
            )

        self.summary_label.setText(
            f"Sessions: {summary['total_sessions']}    "
            f"Unique participant IDs: "
            f"{summary['unique_participants']}\n"
            f"Active: {active['sessions']} sessions "
            f"({active['completed']} completed)    "
            f"Silent: {silent['sessions']} sessions "
            f"({silent['completed']} completed)\n"
            f"Mean completion time: "
            f"Active {mean_text(active, 'duration_seconds')}s | "
            f"Silent {mean_text(silent, 'duration_seconds')}s\n"
            "Note: Detection checks are not unique warnings "
            "or confirmed disclosures."
        )

        self.update_table()
        self.update_chart()

    def update_table(self):
        self.table.setRowCount(
            len(self.records)
        )

        for row, record in enumerate(self.records):
            fields = [
                record.get("participant_id"),
                record.get("condition"),
                record.get("status"),
                record.get("duration_seconds"),
                record.get("messages_sent"),
                record.get("detection_checks"),
                record.get("positive_checks"),
                record.get("warning_exposures"),
            ]

            for column, value in enumerate(fields):
                item = QTableWidgetItem(
                    "N/A" if value is None else str(value)
                )
                self.table.setItem(
                    row, column, item
                )

    def update_chart(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        metrics = {
            "Completion Time": (
                "duration_seconds",
                "Seconds",
            ),
            "Messages Sent": (
                "messages_sent",
                "Messages",
            ),
            "Detection Checks": (
                "detection_checks",
                "Checks",
            ),
            "Positive Detection Checks": (
                "positive_checks",
                "Checks with findings",
            ),
            "Warning Exposures": (
                "warning_exposures",
                "Unique warning episodes",
            ),
            "Warning Hovers": (
                "warning_hovers",
                "Hover interactions",
            ),
        }

        metric, ylabel = metrics[
            self.chart_selector.currentText()
        ]

        groups = {
            "Active": [
                r[metric]
                for r in self.records
                if r["condition"] == "active"
                and r.get(metric) is not None
            ],
            "Silent": [
                r[metric]
                for r in self.records
                if r["condition"] == "silent"
                and r.get(metric) is not None
            ],
        }

        names = []
        averages = []

        for name, values in groups.items():
            if values:
                names.append(name)
                averages.append(
                    sum(values) / len(values)
                )

        if names:
            bars = ax.bar(names, averages)

            for bar, value in zip(bars, averages):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height(),
                    f"{value:.2f}",
                    ha="center",
                    va="bottom"
                )
        else:
            ax.text(
                0.5, 0.5,
                "No available data for this metric",
                ha="center",
                va="center",
                transform=ax.transAxes
            )

        ax.set_ylabel(ylabel)
        ax.set_title(
            f"Mean {self.chart_selector.currentText()} "
            "by Condition"
        )
        ax.grid(axis="y", alpha=0.2)

        self.canvas.draw_idle()
