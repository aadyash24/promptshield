import re
from collections import deque

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QScrollArea,
    QTextEdit,
    QPushButton,
    QSizePolicy,
    QApplication,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal, QTimer, QEvent, QThread, QPoint, QElapsedTimer
from PySide6.QtGui import QCursor, QFontMetrics, QTextCursor, QTextCharFormat, QColor, QIcon, QPainter, QPixmap

from ps.detection.promptshield_client import PromptShieldClient
from ps.rewrite.ollama_rewriter import OllamaRewriter
from ps.warnings.finding_utils import locate_findings
from services.chat_backend import ChatBackend
from ui.theme import study_theme


class DetectionWorker(QThread):
    """Call the detection service outside of the GUI thread."""

    result_ready = Signal(int, object)
    error_occurred = Signal(int, str)

    def __init__(self, client, text, revision):
        super().__init__()
        self.client = client
        self.text = text
        self.revision = revision

    def run(self):
        try:
            result = self.client.detect(self.text)
            self.result_ready.emit(self.revision, result)
        except Exception as error:
            self.error_occurred.emit(self.revision, str(error))


class SafeRewriteWorker(QThread):
    """Rewrite the selected finding and its sentence, then splice it into the draft."""

    result_ready = Signal(int, object)
    error_occurred = Signal(int, str)

    def __init__(self, rewriter, message, finding, other_findings, revision):
        super().__init__()
        self.rewriter = rewriter
        self.message = message
        self.finding = dict(finding)
        self.other_findings = [dict(span) for span in other_findings]
        self.revision = revision

    def run(self):
        try:
            start, end = self.finding["start"], self.finding["end"]
            left, right = 0, len(self.message)
            for boundary in re.finditer(r"(?<=[.!?])[^\S\n]+|\n+", self.message):
                if boundary.end() <= start:
                    left = boundary.end()
                elif boundary.start() >= end:
                    right = boundary.start()
                    break

            context = self.message[left:right]
            target = {**self.finding, "start": start - left, "end": end - left}
            rewritten = self.rewriter.rewrite(context, [target])
            for span in self.other_findings:
                if span["start"] < right and span["end"] > left:
                    value = span["text"]
                    if rewritten.count(value) != context.count(value):
                        raise ValueError("The rewrite changed another highlighted detail.")
            self.result_ready.emit(self.revision, (left, right, rewritten))

        except Exception as error:
            self.error_occurred.emit(self.revision, str(error))
class PrivacyWarningPopup(QFrame):
    """Interactive privacy warning anchored to highlighted text."""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus)
        self.tier = 1
        self.setObjectName("privacyWarningPopup")
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFixedWidth(320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(7)

        self.heading = QLabel()
        self.heading.setObjectName("privacyWarningHeading")
        self.heading.setWordWrap(True)
        self.description = QLabel()
        self.description.setObjectName("privacyWarningDescription")
        self.description.setWordWrap(True)
        self.advice = QLabel("Consider whether this detail is necessary before sending.")
        self.advice.setObjectName("privacyWarningAdvice")
        self.advice.setWordWrap(True)

        layout.addWidget(self.heading)
        layout.addWidget(self.description)
        layout.addWidget(self.advice)
        self.rewrite_button = QPushButton("Rewrite this detail")
        self.rewrite_button.setCursor(Qt.PointingHandCursor)
        self.rewrite_button.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(self.rewrite_button)
        study_theme().changed.connect(self.apply_styles)

    def show_finding(self, finding, anchor):
        tier = self.tier = finding["tier"]
        category = str(finding.get("category", "SENSITIVE")).upper()
        descriptions = {
            "EMAIL": "An email address can identify or provide a way to contact someone.",
            "PHONE": "A phone number can identify or provide a way to contact someone.",
            "MEDICAL": "Health details may reveal sensitive medical information.",
            "FINANCIAL": "Financial details may reveal private financial information.",
            "ACCOUNT": "Account identifiers may be especially sensitive.",
            "PERSONAL": "This detail may reveal personally identifying information.",
        }
        self.heading.setText(f"Potential {category.replace('_', ' ').title()} disclosure · Tier {tier}")
        self.description.setText(descriptions.get(
            category, "This text may contain sensitive personal information."
        ))
        self.apply_styles()
        self.adjustSize()

        # Prefer above the text line, not above the mouse pointer.
        screen = QApplication.screenAt(anchor)
        if screen is None:
            screen = QApplication.primaryScreen()
        bounds = screen.availableGeometry()
        x = max(bounds.left() + 6, min(anchor.x() - 24,
                                        bounds.right() - self.width() - 6))
        y = anchor.y() - self.height() - 12
        if y < bounds.top() + 6:
            y = anchor.y() + 24
        y = min(y, bounds.bottom() - self.height() - 6)
        self.move(x, y)
        self.show()

    def apply_styles(self):
        background, foreground = MessageInput.SEVERITY_COLORS[self.tier]
        self.setStyleSheet(study_theme().stylesheet(f"""
            QFrame#privacyWarningPopup {{
                background-color: $surface;
                border: 2px solid {foreground};
                border-radius: 12px;
            }}
            QLabel {{ border: none; background: transparent; color: $body; }}
            QLabel#privacyWarningHeading {{
                background-color: {background};
                color: {foreground};
                padding: 9px;
                border-radius: 7px;
                font-weight: bold;
                font-size: 13px;
            }}
            QLabel#privacyWarningDescription {{ font-size: 12px; }}
            QLabel#privacyWarningAdvice {{ color: $muted; font-size: 12px; }}
            QPushButton {{ background: $teal; color: $on_primary; padding: 7px; border-radius: 6px; }}
            QPushButton:hover {{ background: $teal_hover; }}
            QPushButton:disabled {{ background: $disabled; }}
        """))


class MessageInput(QTextEdit):
    """Chat input with inline privacy highlights and readable hover cards."""

    send_requested = Signal()
    warning_hover_event = Signal(str, object)
    rewrite_requested = Signal(object)

    SEVERITY_COLORS = {
        1: ("#FEF9C3", "#713F12"),
        2: ("#FED7AA", "#9A3412"),
        3: ("#FECACA", "#991B1B"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_findings = []
        self._hovered_finding_key = None
        self._hover_details = None
        self._hover_timer = QElapsedTimer()
        self._hover_count = 0
        self._privacy_popup = PrivacyWarningPopup(self)
        self._popup_finding = None
        self._warning_dismiss_timer = QTimer(self)
        self._warning_dismiss_timer.setSingleShot(True)
        self._warning_dismiss_timer.setInterval(350)
        self._warning_dismiss_timer.timeout.connect(self._dismiss_if_pointer_left)
        self._privacy_popup.rewrite_button.clicked.connect(self._request_popup_rewrite)
        self._privacy_popup.installEventFilter(self)
        self.viewport().setMouseTracking(True)
        self.viewport().installEventFilter(self)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() == Qt.ShiftModifier:
                super().keyPressEvent(event)
            elif event.modifiers() == Qt.NoModifier:
                self.send_requested.emit()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def highlight_findings(self, spans):
        self.dismiss_warning()
        self.current_findings = []
        selections = []
        message = self.toPlainText()

        for span in spans:
            start = span["start"]
            end = span["end"]
            if start < 0 or end > len(message) or end <= start:
                continue

            start_pos = len(message[:start].encode("utf-16-le")) // 2
            end_pos = len(message[:end].encode("utf-16-le")) // 2
            tier = max(1, min(int(span.get("tier", 1)), 3))
            background, foreground = self.SEVERITY_COLORS[tier]
            cursor = QTextCursor(self.document())
            cursor.setPosition(start_pos)
            cursor.setPosition(end_pos, QTextCursor.KeepAnchor)
            selection = QTextEdit.ExtraSelection()
            selection.cursor = cursor
            fmt = QTextCharFormat()
            fmt.setBackground(QColor(background))
            fmt.setForeground(QColor(foreground))
            selection.format = fmt
            selections.append(selection)
            self.current_findings.append({
                **span, "tier": tier, "qt_start": start_pos, "qt_end": end_pos,
            })

        self.setExtraSelections(selections)

    def clear_highlights(self):
        self.current_findings = []
        self.setExtraSelections([])
        self.dismiss_warning()

    def dismiss_warning(self):
        self._warning_dismiss_timer.stop()
        self._privacy_popup.hide()
        self._finish_warning_hover()

    def set_rewrite_pending(self, pending):
        button = self._privacy_popup.rewrite_button
        button.setEnabled(not pending)
        button.setText("Rewriting…" if pending else "Rewrite this detail")

    def _request_popup_rewrite(self):
        if self._popup_finding is not None:
            self.rewrite_requested.emit(self._popup_finding)

    def _dismiss_if_pointer_left(self):
        if not self._privacy_popup.geometry().contains(QCursor.pos()):
            self.dismiss_warning()

    def _finish_warning_hover(self):
        details = self._hover_details
        self._hover_details = None
        self._hovered_finding_key = None
        self._popup_finding = None
        if details is not None:
            self.warning_hover_event.emit("warning_hover_ended", {
                **details, "duration_ms": self._hover_timer.elapsed(),
            })

    def _finding_at_point(self, point):
        """Hit-test actual displayed text cells, avoiding nearest-cursor snapping."""
        cursor_pos = self.cursorForPosition(point).position()
        for finding in self.current_findings:
            first = finding["qt_start"]
            last = finding["qt_end"]
            if not (first - 1 <= cursor_pos <= last):
                continue
            for pos in range(first, last):
                cursor = QTextCursor(self.document())
                cursor.setPosition(pos)
                left_rect = self.cursorRect(cursor)
                cursor.setPosition(pos + 1)
                right_rect = self.cursorRect(cursor)
                if abs(left_rect.center().y() - right_rect.center().y()) > 3:
                    continue
                x1 = min(left_rect.left(), right_rect.left())
                x2 = max(left_rect.left(), right_rect.left())
                if (x1 - 2 <= point.x() <= x2 + 2 and
                        left_rect.top() - 2 <= point.y() <= left_rect.bottom() + 2):
                    return finding, left_rect
        return None, None

    def _update_hover(self, point):
        finding, rect = self._finding_at_point(point)
        if finding is None:
            if self._hovered_finding_key is not None:
                if not self._warning_dismiss_timer.isActive():
                    self._warning_dismiss_timer.start()
            return

        self._warning_dismiss_timer.stop()
        key = (finding["qt_start"], finding["qt_end"], finding.get("category"))
        if key != self._hovered_finding_key:
            self.dismiss_warning()
            cursor = QTextCursor(self.document())
            cursor.setPosition(finding["qt_start"])
            first_rect = self.cursorRect(cursor)
            if abs(first_rect.center().y() - rect.center().y()) > 3:
                first_rect = rect
            anchor = self.viewport().mapToGlobal(
                QPoint(first_rect.left(), first_rect.top())
            )
            self._privacy_popup.show_finding(finding, anchor)
            if not self._privacy_popup.isVisible():
                return
            self._popup_finding = finding
            self._hovered_finding_key = key
            self._hover_count += 1
            self._hover_details = {
                "hover_id": self._hover_count,
                "category": finding.get("category", "SENSITIVE"),
                "tier": finding["tier"],
            }
            self._hover_timer.start()
            self.warning_hover_event.emit("warning_hovered", self._hover_details.copy())

    def eventFilter(self, watched, event):
        if watched is self.viewport():
            if event.type() == QEvent.MouseMove:
                self._update_hover(event.position().toPoint())
            elif event.type() == QEvent.Leave and self._privacy_popup.isVisible():
                self._warning_dismiss_timer.start()
            elif event.type() in (QEvent.Wheel, QEvent.MouseButtonPress, QEvent.Hide, QEvent.WindowDeactivate):
                self.dismiss_warning()
        elif watched is self._privacy_popup:
            if event.type() == QEvent.Enter:
                self._warning_dismiss_timer.stop()
            elif event.type() == QEvent.Leave:
                self._warning_dismiss_timer.start()
            elif event.type() == QEvent.Hide:
                self._warning_dismiss_timer.stop()
                self._finish_warning_hover()
        return super().eventFilter(watched, event)


class ChatWidget(QWidget):
    message_submitted = Signal(str)
    message_copied = Signal(str)
    detection_completed = Signal(object)
    sent_detection_completed = Signal(object)

    def __init__(self, parent=None, study_condition="active"):
        super().__init__(parent)
        self.setObjectName("chatWidget")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.message_bubbles = []
        self.study_condition = study_condition
        self.detector = PromptShieldClient()
        self.chat_backend = ChatBackend(self)
        self.chat_backend.reply_ready.connect(self.on_chat_reply)
        self.chat_backend.reply_failed.connect(self.on_chat_error)
        self._system_message = {
            "role": "system",
            "content": (
                "You are a helpful writing assistant. Follow the user's instructions "
                "and use the facts they provide in the conversation."
            ),
        }
        self._chat_history = []
        self._awaiting_reply = False
        self._draft_revision = 0
        self._detection_worker = None
        self._pending_sent_checks = deque()
        self._sent_check_id = None
        self._detection_stopped = False
        self._check_queued = False
        self._last_detection_error = None
        self._last_logged_findings = None

        # Safe rewrite state: reuse the exact spans from the completed draft scan.
        self._last_detection_text = None
        self._last_findings = []
        self._last_flagged_spans = []
        self._rewrite_worker = None
        self.rewriter = OllamaRewriter()

        self.setup_ui()
        study_theme().changed.connect(self.apply_styles)
        self.apply_styles()
        self.scroll_area.viewport().installEventFilter(self)

        self.detection_timer = QTimer(self)
        self.detection_timer.setSingleShot(True)
        self.detection_timer.setInterval(500)
        self.detection_timer.timeout.connect(self.run_detection)
        self.message_input.textChanged.connect(self.on_draft_changed)

        QTimer.singleShot(0, self.update_bubble_widths)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(0)

        container = QFrame()
        container.setObjectName("chatContainer")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        header = QWidget()
        header.setObjectName("chatHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 18, 24, 18)
        title = QLabel("AI Assistant")
        title.setObjectName("chatTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()
        container_layout.addWidget(header)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("conversationScroll")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.messages_container = QWidget()
        self.messages_container.setObjectName("messagesContainer")
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(16, 20, 16, 20)
        self.messages_layout.setSpacing(16)
        self.messages_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.messages_container)
        container_layout.addWidget(self.scroll_area, 1)

        input_container = QWidget()
        input_container.setObjectName("inputContainer")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(10)
        self.message_input = MessageInput()
        self.message_input.setObjectName("messageInput")
        self.message_input.setPlaceholderText("Message AI Assistant...")
        self.message_input.setFixedHeight(64)
        self.message_input.setAcceptRichText(False)
        self.message_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.message_input.send_requested.connect(self.send_message)
        self.send_button = QPushButton("➤")
        self.send_button.setObjectName("sendButton")
        self.send_button.setFixedSize(44, 44)
        self.send_button.setCursor(Qt.PointingHandCursor)
        self.send_button.clicked.connect(self.send_message)
        self.message_input.rewrite_requested.connect(self.rewrite_safely)
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        container_layout.addWidget(input_container)
        layout.addWidget(container)

        self.add_message(
            "How can I help you with your writing?",
            sender="assistant",
            show_actions=False,
        )

    def set_study_condition(self, condition):
        if condition not in ("active", "silent"):
            raise ValueError("Condition must be 'active' or 'silent'.")
        self.study_condition = condition
        if condition == "silent":
            self.message_input.clear_highlights()
        elif self.message_input.toPlainText().strip():
            self.detection_timer.start()

    def on_draft_changed(self):
        self._draft_revision += 1
        # Preserve upstream queue behavior and invalidate cached rewrite spans.
        self._check_queued = False
        self._last_detection_text = None
        self._last_findings = []
        self._last_flagged_spans = []
        self.message_input.clear_highlights()
        text = self.message_input.toPlainText()
        if not text.strip():
            self.detection_timer.stop()
            self._last_logged_findings = None
            return
        if not self._detection_stopped:
            self.detection_timer.start()

    def run_detection(self):
        text = self.message_input.toPlainText()
        if self._detection_stopped or not text.strip():
            return
        if self._detection_worker is not None:
            self._check_queued = True
            return
        self._check_queued = False
        self.start_detection(text)

    def check_sent_message(self, message_id, text):
        if self._detection_worker is None:
            self.start_detection(text, message_id)
        else:
            self._pending_sent_checks.append((text, message_id))

    def start_detection(self, text, message_id=None):
        worker = DetectionWorker(self.detector, text, self._draft_revision)
        worker.result_ready.connect(self.on_detection_result)
        worker.error_occurred.connect(self.on_detection_error)
        worker.finished.connect(self.on_detection_finished)
        self._detection_worker = worker
        self._sent_check_id = message_id
        worker.start()

    def on_detection_result(self, revision, result):
        if self._detection_stopped:
            return
        findings = result["findings"]
        if self._sent_check_id is not None:
            self.finish_sent_detection(
                "ok",
                mode=result.get("mode", "unknown"),
                contains_pii=bool(findings),
                finding_count=len(findings),
                categories=sorted({f.get("category", "SENSITIVE") for f in findings}),
                max_tier=max((f.get("tier", 1) for f in findings), default=0),
            )
            return
        if revision != self._draft_revision:
            return

        text = self.message_input.toPlainText()
        spans = locate_findings(text, findings)
        self._last_detection_text = text
        self._last_findings = findings
        self._last_flagged_spans = spans
        self._last_detection_error = None

        # Preserve upstream telemetry deduplication and event payload.
        finding_keys = frozenset(
            (f.get("text", ""), f.get("category", "SENSITIVE"), f.get("tier", 1))
            for f in findings
        )
        if finding_keys != self._last_logged_findings:
            self._last_logged_findings = finding_keys
            self.detection_completed.emit({
                "revision": revision,
                "mode": result.get("mode", "unknown"),
                "finding_count": len(findings),
                "categories": sorted({f.get("category", "SENSITIVE") for f in findings}),
            })

        if self.study_condition == "silent":
            self.message_input.clear_highlights()
            return
        self.message_input.highlight_findings(spans)

    def on_detection_error(self, revision, error):
        if self._detection_stopped:
            return
        if self._sent_check_id is not None:
            self.finish_sent_detection("failed")
            return
        if revision != self._draft_revision:
            return

        self.message_input.clear_highlights()
        self._last_detection_text = None
        self._last_findings = []
        self._last_flagged_spans = []
        if error != self._last_detection_error:
            print("PromptShield detector unavailable:", error)
            self._last_detection_error = error

    def finish_sent_detection(self, status, **details):
        message_id = self._sent_check_id
        self._sent_check_id = None
        self.sent_detection_completed.emit({"message_id": message_id, "status": status, **details})

    def on_detection_finished(self):
        worker = self._detection_worker
        self._detection_worker = None
        if worker is not None:
            worker.deleteLater()
        if self._pending_sent_checks:
            self.start_detection(*self._pending_sent_checks.popleft())
        elif self._check_queued:
            self.run_detection()

    def rewrite_safely(self, finding):
        if self.study_condition != "active" or self._rewrite_worker is not None:
            return
        message = self.message_input.toPlainText()
        if self._last_detection_text != message:
            return
        bounds = (finding["start"], finding["end"])
        other_findings = [
            span for span in self._last_flagged_spans
            if (span["start"], span["end"]) != bounds
        ]
        self.message_input.set_rewrite_pending(True)
        worker = SafeRewriteWorker(
            self.rewriter, message, finding, other_findings, self._draft_revision,
        )
        worker.result_ready.connect(self.on_safe_rewrite_result)
        worker.error_occurred.connect(self.on_safe_rewrite_error)
        worker.finished.connect(self.on_safe_rewrite_finished)
        self._rewrite_worker = worker
        worker.start()

    def on_safe_rewrite_result(self, revision, replacement):
        if revision != self._draft_revision or self.study_condition != "active":
            return
        start, end, text = replacement
        draft = self.message_input.toPlainText()
        cursor = self.message_input.textCursor()
        cursor.setPosition(len(draft[:start].encode("utf-16-le")) // 2)
        cursor.setPosition(len(draft[:end].encode("utf-16-le")) // 2, QTextCursor.KeepAnchor)
        cursor.insertText(text)
        self.message_input.setTextCursor(cursor)
        self.message_input.setFocus()

    def on_safe_rewrite_error(self, revision, error):
        if revision != self._draft_revision:
            return
        QMessageBox.warning(
            self,
            "Safe rewrite failed",
            "PromptShield could not create a rewrite that passed privacy checks. "
            "Your draft has not been changed. Check that Ollama and the detector "
            "are running, then try again.\n\nDetails: " + error,
        )

    def on_safe_rewrite_finished(self):
        worker = self._rewrite_worker
        self._rewrite_worker = None
        if worker is not None:
            worker.deleteLater()
        self.message_input.set_rewrite_pending(False)

    def add_message(self, text, sender="assistant", show_actions=True, action_text=None):
        message_row = QWidget()
        message_row.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        row_layout = QHBoxLayout(message_row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)
        bubble = QFrame()
        bubble.setObjectName("userBubble" if sender == "user" else "assistantBubble")
        bubble.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(14, 12, 14, 12)
        bubble_layout.setSpacing(10)
        message_label = QLabel(text)
        message_label.setTextFormat(Qt.PlainText)
        message_label.setObjectName("messageText")
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        message_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        font = message_label.font()
        font.setPixelSize(14)
        message_label.setFont(font)
        bubble_layout.addWidget(message_label)
        metrics = QFontMetrics(font)
        preferred_width = max((metrics.horizontalAdvance(line) for line in text.split("\n")), default=0) + 36

        if sender == "assistant" and show_actions:
            copy_button = QPushButton()
            copy_button.setObjectName("copyMessageButton")
            copy_button.setIcon(self.copy_icon)
            copy_button.setFixedSize(28, 28)
            copy_button.setCursor(Qt.PointingHandCursor)
            copy_button.setToolTip("Copy to clipboard")
            copy_button.setAccessibleName("Copy to clipboard")
            action_content = text if action_text is None else action_text
            copy_button.clicked.connect(lambda: self.copy_message(action_content))
            bubble_layout.addWidget(copy_button, alignment=Qt.AlignLeft)
            preferred_width = max(preferred_width, 56)

        if sender == "user":
            row_layout.addStretch()
            row_layout.addWidget(bubble)
        else:
            row_layout.addWidget(bubble)
            row_layout.addStretch()
        self.messages_layout.addWidget(message_row)
        self.message_bubbles.append((bubble, preferred_width))
        self.update_bubble_widths()
        QTimer.singleShot(0, self.scroll_to_bottom)

    def copy_message(self, text):
        QApplication.clipboard().setText(text)
        self.message_copied.emit(text)

    def send_message(self):
        text = self.message_input.toPlainText().strip()
        if not text or self.message_input.isReadOnly() or self._awaiting_reply:
            return
        self.add_message(text, sender="user", show_actions=False)
        self.detection_timer.stop()
        self._last_detection_text = None
        self._last_findings = []
        self._last_flagged_spans = []
        self.message_input.clear_highlights()
        self.message_input.clear()
        self.message_submitted.emit(text)
        self._chat_history.append({"role": "user", "content": text})
        self.set_awaiting_reply(True)
        self.chat_backend.request_reply([self._system_message, *self._chat_history])

    def set_awaiting_reply(self, waiting):
        self._awaiting_reply = waiting
        self.send_button.setEnabled(not waiting)
        self.send_button.setText("…" if waiting else "➤")

    def on_chat_reply(self, text):
        self._chat_history.append({"role": "assistant", "content": text})
        self.add_message(text)
        self.set_awaiting_reply(False)

    def on_chat_error(self):
        self._chat_history.pop()
        self.add_message(
            "The local assistant could not reply. Please try again.",
            show_actions=False,
        )
        self.set_awaiting_reply(False)

    def scroll_to_bottom(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_chat(self):
        self.chat_backend.cancel()
        self._chat_history.clear()
        self.set_awaiting_reply(False)
        self.message_bubbles.clear()
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.detection_timer.stop()
        self._last_detection_text = None
        self._last_findings = []
        self._last_flagged_spans = []
        self.message_input.clear()
        self.message_input.clear_highlights()
        self._check_queued = False

    def update_bubble_widths(self):
        viewport_width = self.scroll_area.viewport().width()
        margins = self.messages_layout.contentsMargins()
        available_width = viewport_width - margins.left() - margins.right() - 8
        if available_width <= 0:
            return
        for bubble, preferred_width in self.message_bubbles:
            bubble.setFixedWidth(max(1, int(min(preferred_width, 600, available_width))))

    def eventFilter(self, watched, event):
        if watched is self.scroll_area.viewport() and event.type() == QEvent.Resize:
            self.update_bubble_widths()
        return super().eventFilter(watched, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_bubble_widths()

    def stop_detection(self):
        self._detection_stopped = True
        self.detection_timer.stop()
        self._check_queued = False
        if self._sent_check_id is not None:
            self.finish_sent_detection("interrupted")
        while self._pending_sent_checks:
            _, message_id = self._pending_sent_checks.popleft()
            self.sent_detection_completed.emit({"message_id": message_id, "status": "interrupted"})
        if self._detection_worker is not None and self._detection_worker.isRunning():
            self._detection_worker.wait()

    def shutdown(self):
        self.chat_backend.cancel()
        self.message_input.dismiss_warning()
        self.stop_detection()
        if self._rewrite_worker is not None and self._rewrite_worker.isRunning():
            self._rewrite_worker.wait()

    def closeEvent(self, event):
        self.shutdown()
        super().closeEvent(event)

    def apply_styles(self):
        theme = study_theme()
        copy_pixmap = QPixmap(16, 16)
        copy_pixmap.fill(Qt.transparent)
        with QPainter(copy_pixmap) as painter:
            painter.setPen(QColor(theme.colors["body"]))
            painter.drawPolyline([QPoint(11, 2), QPoint(2, 2), QPoint(2, 11)])
            painter.drawRoundedRect(5, 5, 9, 9, 1, 1)
        self.copy_icon = QIcon(copy_pixmap)
        for button in self.findChildren(QPushButton, "copyMessageButton"):
            button.setIcon(self.copy_icon)
        self.setStyleSheet(theme.stylesheet("""
            QWidget#chatWidget { background-color: $page; }
            QFrame#chatContainer { background-color: $surface; border: 1px solid $border; border-radius: 12px; }
            QWidget#chatHeader { background-color: $surface; }
            QLabel#chatTitle { font-size: 18px; font-weight: bold; color: $heading; }
            QScrollArea#conversationScroll { background-color: $surface; border: none; }
            QWidget#messagesContainer { background-color: $surface; }
            QFrame#userBubble { background-color: $user_bubble; border: none; border-radius: 12px; }
            QFrame#assistantBubble { background-color: $subtle; border: none; border-radius: 12px; }
            QLabel#messageText { font-size: 14px; color: $text; background: transparent; border: none; }
            QWidget#inputContainer { background-color: $surface; }
            QTextEdit#messageInput { background-color: $page; border: 1px solid $control_border; border-radius: 10px; padding: 10px; font-size: 14px; color: $heading; }
            QTextEdit#messageInput:focus { border: 1px solid $accent; }
            QPushButton#sendButton { background-color: $primary; color: $on_primary; border: none; border-radius: 10px; font-size: 20px; }
            QPushButton#sendButton:hover { background-color: $primary_hover; }
            QPushButton#copyMessageButton { background: transparent; border: 1px solid transparent; border-radius: 5px; }
            QPushButton#copyMessageButton:hover, QPushButton#copyMessageButton:focus { background: $hover; border-color: $strong_border; }
        """))
