"""Shared colors and appearance preference for the participant study."""

from string import Template

from PySide6.QtCore import QObject, QSettings, Qt, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


LIGHT = {
    "page": "#F8FAFC",
    "surface": "#FFFFFF",
    "editor": "#FAFBFD",
    "subtle": "#F1F5F9",
    "hover": "#E2E8F0",
    "heading": "#0F172A",
    "text": "#1E293B",
    "body": "#334155",
    "secondary": "#475569",
    "muted": "#64748B",
    "border": "#E2E8F0",
    "control_border": "#CBD5E1",
    "strong_border": "#94A3B8",
    "primary": "#2563EB",
    "primary_hover": "#1D4ED8",
    "accent": "#2563EB",
    "accent_strong": "#1D4ED8",
    "on_primary": "#FFFFFF",
    "disabled": "#94A3B8",
    "disabled_surface": "#CBD5E1",
    "selection": "#BFDBFE",
    "user_bubble": "#DBEAFE",
    "teal": "#0F766E",
    "teal_hover": "#115E59",
    "teal_text": "#115E59",
    "status_error": "#B91C1C",
    "status_ready": "#15803D",
    "status_pending": "#A16207",
}

DARK = {
    "page": "#111827",
    "surface": "#1B2535",
    "editor": "#141D2B",
    "subtle": "#263347",
    "hover": "#34445A",
    "heading": "#F8FAFC",
    "text": "#E2E8F0",
    "body": "#CBD5E1",
    "secondary": "#BCCADE",
    "muted": "#A6B5CA",
    "border": "#34445A",
    "control_border": "#50617A",
    "strong_border": "#8191A8",
    "primary": "#2563EB",
    "primary_hover": "#1D4ED8",
    "accent": "#93C5FD",
    "accent_strong": "#BFDBFE",
    "on_primary": "#FFFFFF",
    "disabled": "#475569",
    "disabled_surface": "#34445A",
    "selection": "#31547C",
    "user_bubble": "#243D60",
    "teal": "#0F766E",
    "teal_hover": "#115E59",
    "teal_text": "#99F6E4",
    "status_error": "#FCA5A5",
    "status_ready": "#86EFAC",
    "status_pending": "#FDE68A",
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
        # Fusion honors the palette for controls that have no study stylesheet.
        if self.dark:
            app.setStyle("Fusion")
        else:
            app.setStyle(self.native_style)

        if not self.dark:
            app.setPalette(app.style().standardPalette())
            return

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


def study_theme():
    app = QApplication.instance()
    if not hasattr(app, "study_theme"):
        app.study_theme = StudyTheme(app)
    return app.study_theme
