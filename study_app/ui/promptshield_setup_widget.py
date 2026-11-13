"""Installation progress and local service startup for the study."""

import json
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QProcess, Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPlainTextEdit, QProgressBar, QPushButton,
    QVBoxLayout, QWidget,
)


PS_ROOT = Path(__file__).resolve().parents[2] / "ps"
COMPONENTS = {
    "detector": "Sensitive information detector · b-tok2",
    "ollama": "Local model runtime · Ollama",
    "qwen": "Rewrite and chat model · Qwen 2.5 3B",
}
STATUS = {
    "checking": "Checking", "installed": "Installed", "missing": "Required",
    "downloading": "Downloading", "verifying": "Verifying",
    "starting": "Starting", "ready": "Ready", "failed": "Failed",
}


class PromptShieldSetupWidget(QWidget):
    ready = Signal(str)
    service_lost = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._phase = ""
        self._buffer = bytearray()
        self._failed = False
        self._ready = False
        self._closing = False
        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._read_output)
        self._process.finished.connect(self._finished)
        self._process.errorOccurred.connect(self._process_error)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.addStretch()
        card = QFrame()
        card.setObjectName("setupCard")
        card.setMinimumWidth(540)
        card.setMaximumWidth(680)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        title = QLabel("PromptShield Setup")
        title.setObjectName("setupTitle")
        layout.addWidget(title)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.summary.setTextFormat(Qt.PlainText)
        layout.addWidget(self.summary)

        self.status_labels = {}
        for component, name in COMPONENTS.items():
            row = QHBoxLayout()
            row.addWidget(QLabel(name))
            row.addStretch()
            status = QLabel("Pending")
            status.setObjectName("setupStatus")
            row.addWidget(status)
            self.status_labels[component] = status
            layout.addLayout(row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(7)
        layout.addWidget(self.progress)

        actions = QHBoxLayout()
        details_button = QPushButton("Show details")
        details_button.setCheckable(True)
        actions.addWidget(details_button)
        actions.addStretch()
        self.action = QPushButton()
        self.action.setObjectName("setupAction")
        self.action.hide()
        actions.addWidget(self.action)
        layout.addLayout(actions)

        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setMaximumBlockCount(500)
        self.details.setMaximumHeight(160)
        self.details.hide()
        details_button.toggled.connect(self.details.setVisible)
        details_button.toggled.connect(
            lambda expanded: details_button.setText("Hide details" if expanded else "Show details")
        )
        layout.addWidget(self.details)
        outer.addWidget(card, alignment=Qt.AlignHCenter)
        outer.addStretch()
        self.setStyleSheet("""
            QFrame#setupCard { background: white; border: 1px solid #CBD5E1; border-radius: 12px; }
            QLabel { color: #334155; }
            QLabel#setupTitle { color: #0F172A; font-size: 24px; font-weight: bold; }
            QLabel#setupStatus { color: #115E59; font-weight: bold; }
            QPushButton { padding: 7px 12px; }
            QPushButton#setupAction { background: #0F766E; color: white; border-radius: 6px; }
            QPushButton#setupAction:hover { background: #115E59; }
        """)

    def start(self):
        for label in self.status_labels.values():
            label.setText("Checking")
        self._run("launch", sys.executable, ["-u", str(PS_ROOT / "launch.py"), "--gui"])

    def _install(self):
        self._run("install", "powershell.exe", [
            "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
            "-File", str(PS_ROOT / "setup.ps1"), "-JsonProgress",
        ])

    def _run(self, phase, program, args):
        self._phase = phase
        self._failed = False
        self._ready = False
        self._buffer.clear()
        self.action.hide()
        self.progress.show()
        self.summary.setText(
            "Installing missing components…" if phase == "install" else "Checking and starting local services…"
        )
        self._process.start(program, args)

    def _read_output(self):
        self._buffer.extend(bytes(self._process.readAllStandardOutput()))
        lines = self._buffer.split(b"\n")
        self._buffer = lines.pop()
        for line in lines:
            self._handle_line(line)

    def _handle_line(self, line):
        text = line.decode("utf-8", errors="replace").strip()
        if not text:
            return
        try:
            event = json.loads(text)
        except ValueError:
            event = None
        if not isinstance(event, dict) or not {"component", "state", "message"} <= event.keys():
            self.details.appendPlainText(text)
            return
        component, state, message = (event[key] for key in ("component", "state", "message"))
        self.details.appendPlainText(message)
        if component in self.status_labels and state in STATUS:
            self.status_labels[component].setText(STATUS[state])
        self.summary.setText(message)
        self._failed |= state == "failed"
        if component == "setup" and state == "ready" and not self._closing:
            self._ready = True
            self.progress.hide()
            self.ready.emit(event["ollama_model"])

    def _offer(self, title, action):
        self.progress.hide()
        self.action.setText(title)
        self.action.clicked.connect(action, Qt.SingleShotConnection)
        self.action.show()

    def _finished(self, code, status):
        self._read_output()
        self._handle_line(self._buffer)
        self._buffer.clear()
        if self._closing:
            return
        if status == QProcess.NormalExit and self._phase == "install" and code == 0:
            self.start()
        elif status == QProcess.NormalExit and self._phase == "launch" and code == 3:
            self.summary.setText("Install the missing components to continue.")
            self._offer("Install missing components", self._install)
        else:
            if not self._failed:
                self.summary.setText(f"PromptShield {self._phase} stopped (exit code {code}). See details.")
            if self._ready:
                self._offer("Retry", self.start)
                self.service_lost.emit()
            else:
                action = self._install if self._phase == "install" else self.start
                self._offer("Retry", action)

    def _process_error(self, error):
        if error == QProcess.FailedToStart and not self._closing:
            self.summary.setText(self._process.errorString())
            self._offer("Retry", self._install if self._phase == "install" else self.start)

    def shutdown(self):
        self._closing = True
        if self._process.state() == QProcess.NotRunning:
            return
        if self._phase == "launch":
            self._process.write(b"stop\n")
            self._process.closeWriteChannel()
            if self._process.waitForFinished(8000):
                return
        if sys.platform == "win32" and self._process.processId():
            subprocess.run(
                ["taskkill.exe", "/PID", str(self._process.processId()), "/T", "/F"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
            )
        self._process.kill()
        self._process.waitForFinished(2000)
