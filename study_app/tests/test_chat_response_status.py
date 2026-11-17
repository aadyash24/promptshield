import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from ui.chat_widget import ChatWidget
from ui.theme import study_theme


class ChatResponseStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        study_theme()

    def make_widget(self):
        widget = ChatWidget()
        widget.resize(600, 500)
        widget.show()
        self.app.processEvents()
        self.addCleanup(widget.close)
        self.addCleanup(widget.shutdown)
        return widget

    def test_status_appears_while_waiting_and_clears_on_reply(self):
        widget = self.make_widget()
        widget.message_input.setPlainText("Help me draft this.")
        widget.detection_timer.stop()
        with patch.object(widget.chat_backend, "request_reply"):
            widget.send_message()
        self.assertIsNotNone(widget._response_status_row)
        self.assertEqual(widget._response_status_label.accessibleName(), "AI is responding")
        self.assertFalse(widget.send_button.isEnabled())
        widget.on_chat_reply("Here is a draft.")
        self.assertIsNone(widget._response_status_row)
        self.assertTrue(widget.send_button.isEnabled())

    def test_status_clears_on_error_and_new_content_scrolls_down(self):
        widget = self.make_widget()
        widget.set_awaiting_reply(True)
        widget._chat_history.append({"role": "user", "content": "test"})
        widget.on_chat_error()
        QTest.qWait(60)
        self.assertIsNone(widget._response_status_row)
        scrollbar = widget.scroll_area.verticalScrollBar()
        self.assertEqual(scrollbar.value(), scrollbar.maximum())
