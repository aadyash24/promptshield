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
from PySide6.QtGui import QFontMetrics, QTextCursor, QTextCharFormat, QColor

from services.promptshield_client import PromptShieldClient
from services.chat_backend import ChatBackend
from services.finding_utils import locate_findings
from services.ollama_rewriter import OllamaRewriter

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
    """Rewrite the original message using the exact spans from its completed scan."""

    result_ready = Signal(int, object)
    error_occurred = Signal(int, str)

    def __init__(self, rewriter, message, flagged_spans, revision):
        super().__init__()
        self.rewriter = rewriter
        self.message = message
        self.flagged_spans = [dict(span) for span in flagged_spans]
        self.revision = revision

    def run(self):
        try:
            if not self.flagged_spans:
                self.result_ready.emit(self.revision, {
                    "status": "no_findings",
                    "text": self.message,
                    "finding_count": 0,
                })
                return

            # Send the unchanged draft and the exact spans from the scan already
            # shown in the UI. Do not run a second detection pass or alter text.
            rewritten = self.rewriter.rewrite(
                self.message,
                self.flagged_spans,
            )

            self.result_ready.emit(self.revision, {
                "status": "ok",
                "text": rewritten,
                "finding_count": len(self.flagged_spans),
            })

        except Exception as error:
            self.error_occurred.emit(self.revision, str(error))
class PrivacyWarningPopup(QFrame):
    """Larger, non-interactive privacy warning anchored to highlighted text."""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint)
        self.setObjectName("privacyWarningPopup")
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
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

    def show_finding(self, finding, anchor):
        tier = finding["tier"]
        category = str(finding.get("category", "SENSITIVE")).upper()
        descriptions = {
            "EMAIL": "An email address can identify or provide a way to contact someone.",
            "PHONE": "A phone number can identify or provide a way to contact someone.",
            "MEDICAL": "Health details may reveal sensitive medical information.",
            "FINANCIAL": "Financial details may reveal private financial information.",
            "ACCOUNT": "Account identifiers may be especially sensitive.",
            "PERSONAL": "This detail may reveal personally identifying information.",
        }
        background, foreground = MessageInput.SEVERITY_COLORS[tier]
        self.heading.setText(f"Potential {category.replace('_', ' ').title()} disclosure · Tier {tier}")
        self.description.setText(descriptions.get(
            category, "This text may contain sensitive personal information."
        ))
        self.setStyleSheet(f"""
            QFrame#privacyWarningPopup {{
                background-color: #FFFFFF;
                border: 2px solid {foreground};
                border-radius: 12px;
            }}
            QLabel {{ border: none; background: transparent; color: #334155; }}
            QLabel#privacyWarningHeading {{
                background-color: {background};
                color: {foreground};
                padding: 9px;
                border-radius: 7px;
                font-weight: bold;
                font-size: 13px;
            }}
            QLabel#privacyWarningDescription {{ font-size: 12px; }}
            QLabel#privacyWarningAdvice {{ color: #64748B; font-size: 12px; }}
        """)
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


class MessageInput(QTextEdit):
    """Chat input with inline privacy highlights and readable hover cards."""

    send_requested = Signal()
    warning_hover_event = Signal(str, object)

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
        self._privacy_popup.hide()
        self._finish_warning_hover()

    def _finish_warning_hover(self):
        details = self._hover_details
        self._hover_details = None
        self._hovered_finding_key = None
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
                self.dismiss_warning()
            return

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
            elif event.type() in (
                QEvent.Leave, QEvent.Wheel, QEvent.MouseButtonPress,
                QEvent.Hide, QEvent.WindowDeactivate,
            ):
                self.dismiss_warning()
        elif watched is self._privacy_popup and event.type() == QEvent.Hide:
            self._finish_warning_hover()
        return super().eventFilter(watched, event)


class ChatWidget(QWidget):
    message_submitted = Signal(str)
    insert_requested = Signal(str)
    replace_requested = Signal(str)
    detection_completed = Signal(object)
    sent_detection_completed = Signal(object)

    def __init__(self, parent=None, study_condition="active", task_description=""):
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
                "You are a writing assistant for a fictional role-play exercise. "
                f"Task: {task_description} "
                "Help the user draft and revise a concise, professional letter in plain text. "
                "If the user gives a payment schedule, quote their schedule wording verbatim "
                "inside the letter. Keep each payment amount paired with its original date. "
                "Use only facts supplied by the user. Omit any discussion of attachments, "
                "supporting documents, or receipts unless the user asks for it. "
                "Use placeholders for missing details. When drafting or revising, "
                "return the letter directly and apply the requested changes."
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
        self.task_label = QLabel("Financial Hardship Request")
        self.task_label.setObjectName("chatTaskLabel")
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.task_label)
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
        self.rewrite_button = QPushButton("Rewrite safely")
        self.rewrite_button.setObjectName("rewriteButton")
        self.rewrite_button.setCursor(Qt.PointingHandCursor)
        self.rewrite_button.setFixedHeight(44)
        self.rewrite_button.setMinimumWidth(118)
        self.rewrite_button.setEnabled(False)
        self.rewrite_button.clicked.connect(self.rewrite_safely)
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.rewrite_button)
        input_layout.addWidget(self.send_button)
        container_layout.addWidget(input_container)
        layout.addWidget(container)

        self.add_message(
            "Hello! I can help you draft and improve Maya's financial "
            "hardship letter. What would you like to work on first?",
            sender="assistant",
            show_actions=False,
        )

    def set_study_condition(self, condition):
        if condition not in ("active", "silent"):
            raise ValueError("Condition must be 'active' or 'silent'.")
        self.study_condition = condition
        self.rewrite_button.setVisible(condition == "active")
        if condition == "silent":
            self.message_input.clear_highlights()
            self.rewrite_button.setEnabled(False)
        elif self.message_input.toPlainText().strip():
            self.detection_timer.start()

    def on_draft_changed(self):
        self._draft_revision += 1
        # Preserve upstream queue behavior and invalidate cached rewrite spans.
        self._check_queued = False
        self._last_detection_text = None
        self._last_findings = []
        self._last_flagged_spans = []
        self.rewrite_button.setEnabled(False)
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
        self.rewrite_button.setEnabled(
            self.study_condition == "active" and bool(spans)
        )
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
            self.rewrite_button.setEnabled(False)
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
        self.rewrite_button.setEnabled(False)
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

    def rewrite_safely(self):
        """Rewrite the current draft using the exact spans from its completed scan."""
        if self.study_condition != "active":
            return
        message = self.message_input.toPlainText()
        if not message.strip() or self._rewrite_worker is not None:
            return
        if self._last_detection_text != message or not self._last_flagged_spans:
            QMessageBox.information(
                self,
                "Still checking your message",
                "Wait for the privacy scan to finish, then try Rewrite safely again.",
            )
            self.detection_timer.start()
            return

        self.rewrite_button.setEnabled(False)
        self.rewrite_button.setText("Rewriting…")
        worker = SafeRewriteWorker(
            self.rewriter,
            message,
            self._last_flagged_spans,
            self._draft_revision,
        )
        worker.result_ready.connect(self.on_safe_rewrite_result)
        worker.error_occurred.connect(self.on_safe_rewrite_error)
        worker.finished.connect(self.on_safe_rewrite_finished)
        self._rewrite_worker = worker
        worker.start()

    def on_safe_rewrite_result(self, revision, result):
        if revision != self._draft_revision:
            return
        if result.get("status") == "no_findings":
            self._last_detection_text = None
            self._last_findings = []
            self._last_flagged_spans = []
            QMessageBox.information(
                self,
                "No sensitive information detected",
                "The detector did not find any supported sensitive information in this message.",
            )
            return

        rewritten_text = result.get("text", "")
        self.add_message(
            rewritten_text,
            sender="assistant",
            show_actions=True,
            action_text=rewritten_text,
        )

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
        self.rewrite_button.setText("Rewrite safely")
        current_text = self.message_input.toPlainText()
        self.rewrite_button.setEnabled(
            self.study_condition == "active"
            and bool(self._last_flagged_spans)
            and self._last_detection_text == current_text
        )

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
            actions_container = QWidget()
            actions_container.setObjectName("messageActions")
            actions_layout = QVBoxLayout(actions_container)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(6)
            insert_button = QPushButton("Insert into Editor")
            insert_button.setObjectName("insertButton")
            insert_button.setCursor(Qt.PointingHandCursor)
            insert_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            replace_button = QPushButton("Replace Draft")
            replace_button.setObjectName("replaceButton")
            replace_button.setCursor(Qt.PointingHandCursor)
            replace_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            action_content = text if action_text is None else action_text
            insert_button.clicked.connect(lambda checked=False, content=action_content: self.insert_requested.emit(content))
            replace_button.clicked.connect(lambda checked=False, content=action_content: self.replace_requested.emit(content))
            actions_layout.addWidget(insert_button)
            actions_layout.addWidget(replace_button)
            bubble_layout.addWidget(actions_container)
            preferred_width = max(preferred_width, 190)

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

    def send_message(self):
        text = self.message_input.toPlainText().strip()
        if not text or self.message_input.isReadOnly() or self._awaiting_reply:
            return
        self.add_message(text, sender="user", show_actions=False)
        self.detection_timer.stop()
        self._last_detection_text = None
        self._last_findings = []
        self._last_flagged_spans = []
        self.rewrite_button.setEnabled(False)
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
        self.rewrite_button.setEnabled(False)
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
        self.setStyleSheet("""
            QWidget#chatWidget { background-color: #F8FAFC; }
            QFrame#chatContainer { background-color: white; border: 1px solid #E2E8F0; border-radius: 12px; }
            QWidget#chatHeader { background-color: white; }
            QLabel#chatTitle { font-size: 18px; font-weight: bold; color: #0F172A; }
            QLabel#chatTaskLabel { background-color: #DBEAFE; color: #1D4ED8; padding: 5px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; }
            QScrollArea#conversationScroll { background-color: white; border: none; }
            QWidget#messagesContainer { background-color: white; }
            QFrame#userBubble { background-color: #DBEAFE; border: none; border-radius: 12px; }
            QFrame#assistantBubble { background-color: #F1F5F9; border: none; border-radius: 12px; }
            QLabel#messageText { font-size: 14px; color: #1E293B; background: transparent; border: none; }
            QWidget#messageActions { background: transparent; border: none; }
            QWidget#inputContainer { background-color: white; }
            QTextEdit#messageInput { background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 10px; padding: 10px; font-size: 14px; color: #0F172A; }
            QTextEdit#messageInput:focus { border: 1px solid #2563EB; }
            QPushButton#sendButton { background-color: #2563EB; color: white; border: none; border-radius: 10px; font-size: 20px; }
            QPushButton#sendButton:hover { background-color: #1D4ED8; }
            QPushButton#rewriteButton { background-color: #0F766E; color: white; border: none; border-radius: 9px; padding: 8px 12px; font-size: 12px; font-weight: bold; }
            QPushButton#rewriteButton:hover { background-color: #115E59; }
            QPushButton#rewriteButton:disabled { background-color: #94A3B8; color: #F8FAFC; }
            QPushButton#insertButton { background-color: #2563EB; color: white; border: none; border-radius: 6px; padding: 7px 8px; font-size: 11px; }
            QPushButton#insertButton:hover { background-color: #1D4ED8; }
            QPushButton#replaceButton { background-color: #FFFFFF; color: #334155; border: 1px solid #CBD5E1; border-radius: 6px; padding: 7px 8px; font-size: 11px; }
            QPushButton#replaceButton:hover { background-color: #E2E8F0; }
        """)
