"""Local chat completions for the desktop study assistant."""

import json
import os

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkProxy, QNetworkReply, QNetworkRequest


class ChatBackend(QObject):
    reply_ready = Signal(str)
    reply_failed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = os.environ.get("PROMPTSHIELD_CHAT_MODEL", "qwen2.5:3b")
        self.url = QUrl(os.environ.get(
            "PROMPTSHIELD_CHAT_URL", "http://127.0.0.1:11434/v1/chat/completions"
        ))
        self.network = QNetworkAccessManager(self)
        self.network.setProxy(QNetworkProxy(QNetworkProxy.NoProxy))
        self._reply = None

    def request_reply(self, messages):
        if (self.url.scheme() not in ("http", "https")
                or self.url.host() not in ("127.0.0.1", "::1", "localhost")):
            self.reply_failed.emit()
            return

        request = QNetworkRequest(self.url)
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        request.setAttribute(QNetworkRequest.RedirectPolicyAttribute, QNetworkRequest.ManualRedirectPolicy)
        request.setTransferTimeout(60_000)
        body = json.dumps({
            "model": self.model,
            "messages": messages,
            "stream": False,
            "temperature": 0.2,
            "max_tokens": 512,
        }).encode("utf-8")
        reply = self.network.post(request, body)
        self._reply = reply
        reply.finished.connect(lambda: self.finish_reply(reply))

    def finish_reply(self, reply):
        reply.deleteLater()
        if reply is not self._reply:
            return
        self._reply = None
        if (reply.error() != QNetworkReply.NoError
                or reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) != 200):
            self.reply_failed.emit()
            return
        try:
            text = json.loads(bytes(reply.readAll()))["choices"][0]["message"]["content"]
        except (ValueError, TypeError, KeyError, IndexError):
            self.reply_failed.emit()
            return
        if not isinstance(text, str) or not text.strip():
            self.reply_failed.emit()
            return
        self.reply_ready.emit(text.strip())

    def cancel(self):
        reply = self._reply
        self._reply = None
        if reply is not None:
            reply.abort()
