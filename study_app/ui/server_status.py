"""Live status for the detector and rewrite server."""

import json

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import QLabel


class ServerStatus(QLabel):
    def __init__(self, detector_url, rewriter, parent=None):
        super().__init__("●  Services", parent)
        self.services = {
            "PromptShield detector": (detector_url, "/health"),
            "Ollama rewrite": (rewriter.base_url, "/api/tags"),
        }
        self.model = rewriter.model
        self.statuses = dict.fromkeys(self.services, "Checking")
        self.network = QNetworkAccessManager(self)
        self.timer = QTimer(self)
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self.check_services)
        self.update_indicator()

    def showEvent(self, event):
        super().showEvent(event)
        self.timer.start()
        self.check_services()

    def hideEvent(self, event):
        self.timer.stop()
        super().hideEvent(event)

    def check_services(self):
        for name, (base_url, path) in self.services.items():
            request = QNetworkRequest(QUrl(base_url + path))
            request.setTransferTimeout(2500)
            reply = self.network.get(request)
            reply.finished.connect(lambda name=name, reply=reply: self.finish_check(name, reply))

    def finish_check(self, name, reply):
        reply.deleteLater()
        status = "Unavailable"
        if reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) == 200:
            try:
                payload = json.loads(bytes(reply.readAll()))
                if name == "PromptShield detector":
                    mode = payload.get("mode")
                    if payload.get("ok") is True:
                        status = "Ready" if mode == "token" else f"Degraded ({mode or 'unknown mode'})"
                elif any(model.get("name") == self.model for model in payload.get("models", [])):
                    status = "Ready"
                else:
                    status = f"Model missing ({self.model})"
            except (ValueError, TypeError, AttributeError):
                status = "Invalid response"
        self.statuses[name] = status
        self.update_indicator()

    def update_indicator(self):
        statuses = self.statuses.values()
        if "Unavailable" in statuses or "Invalid response" in statuses:
            color, summary = "#B91C1C", "Services unavailable"
        elif all(status == "Ready" for status in statuses):
            color, summary = "#15803D", "Services ready"
        else:
            color, summary = "#A16207", "Services checking or degraded"
        self.setText(f'<span style="color:{color}">●</span> Services')
        self.setAccessibleName(summary)
        self.setToolTip("\n".join(
            f"{name} · {url} · {self.statuses[name]}"
            for name, (url, _) in self.services.items()
        ))
