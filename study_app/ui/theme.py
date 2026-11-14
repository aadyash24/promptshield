"""Shared colors and appearance preference for the participant study."""

from string import Template

from PySide6.QtCore import QObject, QSettings, Qt, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


# Tennessee Orange and Smokey: https://brand.utk.edu/standards/colors/
# Supporting neutrals adapt the palette for readable light and dark controls.
LIGHT = {
    "page": "#F5F5F3",
    "surface": "#FFFFFF",
    "editor": "#FCFCFA",
    "subtle": "#F0F0ED",
    "hover": "#E5E5E1",
    "heading": "#4B4B4B",
    "text": "#404040",
    "body": "#4B4B4B",
    "secondary": "#555555",
    "muted": "#626262",
    "border": "#DCDCD7",
    "control_border": "#989892",
    "strong_border": "#73736E",
    "primary": "#FF8200",
    "primary_hover": "#FF8200",
    "accent": "#767670",
    "accent_strong": "#4B4B4B",
    "on_primary": "#333333",
    "disabled": "#D2D2CC",
    "disabled_surface": "#DDDDD7",
    "selection": "#E2E2DB",
    "user_bubble": "#F4EBDD",
    "teal": "#FF8200",
    "teal_hover": "#FF8200",
    "teal_text": "#4B4B4B",
    "status_error": "#B91C1C",
    "status_ready": "#15803D",
    "status_pending": "#8A5900",
    "brand": "#FF8200"
}

DARK = {
    "page": "#202020",
    "surface": "#2B2B2B",
    "editor": "#242424",
    "subtle": "#363636",
    "hover": "#454545",
    "heading": "#FFFFFF",
    "text": "#F2F2EF",
    "body": "#DDDDD8",
    "secondary": "#CECEC8",
    "muted": "#B8B8B2",
    "border": "#494945",
    "control_border": "#85857E",
    "strong_border": "#A0A098",
    "primary": "#FF8200",
    "primary_hover": "#FF8200",
    "accent": "#FF8200",
    "accent_strong": "#FF8200",
    "on_primary": "#333333",
    "disabled": "#54544F",
    "disabled_surface": "#454541",
    "selection": "#5A4936",
    "user_bubble": "#42372B",
    "teal": "#FF8200",
    "teal_hover": "#FF8200",
    "teal_text": "#FF8200",
    "status_error": "#FCA5A5",
    "status_ready": "#86EFAC",
    "status_pending": "#FDE68A",
    "brand": "#FF8200"
}


class StudyTheme(QObject):
    changed = Signal()

    def __init__(self, app):
        super().__init__(app)
        self.native_style = app.style().name()
        self.settings = QSettings("PromptShield", "Study")
        self.dark = self.settings.value("appearance/dark", False, type=bool)
        self._apply_palette()

    @property
    def colors(self):
        return DARK if self.dark else LIGHT

    def stylesheet(self, source):
        return Template(source).substitute(self.colors)

    def set_dark(self, dark):
        if self.dark == dark:
            return
        self.dark = dark
        self.settings.setValue("appearance/dark", dark)
        self._apply_palette()
        self.changed.emit()

    def _apply_palette(self):
        app = self.parent()
        app.styleHints().setColorScheme(Qt.ColorScheme.Dark if self.dark else Qt.ColorScheme.Light)
        # One control style prevents native Windows controls clashing with the cards.
        app.setStyle("Fusion")

        palette = QPalette(app.style().standardPalette())
        roles = {
            "Window": "page", "WindowText": "text", "Base": "editor",
            "AlternateBase": "subtle", "Text": "text", "Button": "subtle",
            "ButtonText": "text", "ToolTipBase": "surface", "ToolTipText": "text",
            "Highlight": "selection", "HighlightedText": "heading",
            "PlaceholderText": "muted", "Link": "accent", "LinkVisited": "accent_strong",
            "Light": "strong_border", "Midlight": "control_border", "Mid": "border",
            "Dark": "page", "Shadow": "editor",
        }
        for role, color in roles.items():
            palette.setColor(getattr(QPalette.ColorRole, role), QColor(self.colors[color]))
        for role in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
            palette.setColor(QPalette.Disabled, role, QColor(self.colors["muted"]))
        app.setPalette(palette)
        app.setStyleSheet(self.stylesheet("""
            QToolTip { background: $surface; color: $text; border: 1px solid $control_border; padding: 7px; }
            QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
            QScrollBar::handle:vertical { background: $control_border; min-height: 30px; border-radius: 3px; }
            QScrollBar::handle:vertical:hover { background: $strong_border; }
            QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
            QScrollBar::handle:horizontal { background: $control_border; min-width: 30px; border-radius: 3px; }
            QScrollBar::handle:horizontal:hover { background: $strong_border; }
            QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
            QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
            QMessageBox { background: $surface; }
            QMessageBox QLabel { color: $body; }
            QMessageBox QPushButton { background: $subtle; color: $text; border: 1px solid $control_border; border-radius: 6px; padding: 7px 16px; min-width: 65px; }
            QMessageBox QPushButton:hover { background: $hover; }
            QMessageBox QPushButton:focus { border: 2px solid $accent_strong; }
            QComboBox QAbstractItemView { background: $surface; color: $text; border: 1px solid $control_border; selection-background-color: $selection; selection-color: $heading; padding: 4px; }
        """))


def study_theme():
    app = QApplication.instance()
    if not hasattr(app, "study_theme"):
        app.study_theme = StudyTheme(app)
    return app.study_theme
