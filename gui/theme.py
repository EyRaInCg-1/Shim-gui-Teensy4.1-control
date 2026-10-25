# theme.py
# Shared look & feel: warm neutral palette with a terracotta accent.
import re

from PyQt5.QtGui import QColor, QFont, QPalette
from PyQt5.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

FONT_FAMILY = "Segoe UI"
FONT_SIZE_PT = 10  # Point sizes follow the OS display scaling, so text looks the same on any screen
SERIF_FAMILY = "Georgia"
MONO_FAMILY = "Consolas"

BG = "#FAF9F5"
SURFACE = "#FFFFFF"
SURFACE_MUTED = "#F3F1EA"
BORDER = "#E6E3DA"
BORDER_STRONG = "#D4D0C4"
TEXT = "#1F1E1D"
TEXT_SECONDARY = "#6F6D66"
TEXT_MUTED = "#A8A59C"
ACCENT = "#D97757"
ACCENT_HOVER = "#C96442"
ACCENT_PRESSED = "#B4552F"
ACCENT_DISABLED = "#EDC9BA"
ACCENT_SOFT = "#F7E6DE"
SUCCESS = "#4E9A6A"
SUCCESS_SOFT = "#E3F0E6"
DANGER = "#C8553D"


def dpi_scale():
    screen = QApplication.primaryScreen()
    return screen.logicalDotsPerInch() / 96.0 if screen else 1.0


def px(value):
    """Scale a pixel length designed at 100% display scaling to the current DPI."""
    return max(1, round(value * dpi_scale()))


STYLESHEET = """
QToolTip {
    background: @SURFACE; color: @TEXT; border: 1px solid @BORDER; padding: 4px 8px;
}

/* ---------- Headings ---------- */
QLabel#AppTitle {
    font-family: '@SERIF_FAMILY'; font-size: 17pt; color: @TEXT;
}
QLabel#AppSubtitle, QLabel#Hint {
    color: @TEXT_SECONDARY;
}
QLabel#SectionTitle {
    color: @TEXT_SECONDARY; font-size: 8pt; font-weight: 600;
}
QLabel#FieldLabel {
    color: @TEXT_SECONDARY;
}

/* ---------- Cards ---------- */
QFrame#Card {
    background: @SURFACE; border: 1px solid @BORDER; border-radius: 12px;
}

/* ---------- Buttons ---------- */
QPushButton {
    background: @SURFACE; color: @TEXT;
    border: 1px solid @BORDER_STRONG; border-radius: 8px;
    padding: 7px 14px; font-weight: 600;
}
QPushButton:hover { background: @SURFACE_MUTED; }
QPushButton:pressed { background: @BORDER; }
QPushButton:disabled { background: @BG; color: @TEXT_MUTED; border-color: @BORDER; }
QPushButton:checked { background: @ACCENT; color: white; border-color: @ACCENT; }
QPushButton:checked:hover { background: @ACCENT_HOVER; border-color: @ACCENT_HOVER; }

QPushButton[variant="primary"] {
    background: @ACCENT; color: white; border: 1px solid @ACCENT;
}
QPushButton[variant="primary"]:hover { background: @ACCENT_HOVER; border-color: @ACCENT_HOVER; }
QPushButton[variant="primary"]:pressed { background: @ACCENT_PRESSED; border-color: @ACCENT_PRESSED; }
QPushButton[variant="primary"]:disabled { background: @ACCENT_DISABLED; border-color: @ACCENT_DISABLED; color: white; }

QPushButton[variant="ghost"] {
    background: transparent; border: none; color: @TEXT_SECONDARY; padding: 2px 8px;
}
QPushButton[variant="ghost"]:hover { color: @ACCENT_HOVER; }
QPushButton[variant="ghost"]:disabled { color: @TEXT_MUTED; }

QPushButton[variant="chip"] {
    background: @SURFACE; color: @TEXT_SECONDARY;
    border: 1px solid @BORDER_STRONG; border-radius: 8px;
    padding: 4px 12px; font-weight: 600;
}
QPushButton[variant="chip"]:hover { border-color: @ACCENT; color: @ACCENT_HOVER; }
QPushButton[variant="chip"]:checked,
QPushButton[variant="chip"]:checked:hover { background: @ACCENT_SOFT; color: @ACCENT_PRESSED; border-color: @ACCENT; }

/* ---------- Inputs ---------- */
QLineEdit {
    background: @SURFACE; color: @TEXT;
    border: 1px solid @BORDER_STRONG; border-radius: 8px;
    padding: 6px 8px;
    selection-background-color: @ACCENT_SOFT; selection-color: @TEXT;
}
QLineEdit:focus { border-color: @ACCENT; }
QLineEdit:disabled { background: @BG; color: @TEXT_SECONDARY; border-color: @BORDER; }

QTextEdit {
    background: @SURFACE; color: @TEXT; border: none;
    selection-background-color: @ACCENT_SOFT; selection-color: @TEXT;
}
QTextEdit#Log {
    font-family: '@MONO_FAMILY', 'Cascadia Mono', monospace; font-size: 9pt;
}

/* ---------- Status pill & badge ---------- */
QLabel#StatusPill {
    border-radius: 12px; padding: 5px 12px; font-weight: 600;
    background: @SURFACE_MUTED; color: @TEXT_SECONDARY;
}
QLabel#StatusPill[state="detected"] { background: @ACCENT_SOFT; color: @ACCENT_PRESSED; }
QLabel#StatusPill[state="connected"] { background: @SUCCESS_SOFT; color: @SUCCESS; }

QLabel#Badge {
    background: @ACCENT_SOFT; color: @ACCENT_PRESSED;
    border-radius: 9px; padding: 2px 10px; font-weight: 600;
}

/* ---------- Channel cards ---------- */
QFrame#ChannelCard {
    background: @SURFACE; border: 1px solid @BORDER; border-radius: 10px;
}
QFrame#ChannelCard[calibrated="false"] { background: @SURFACE_MUTED; }
QLabel#ChannelTitle { color: @TEXT; font-weight: 700; }
QLabel#ChannelTitle:hover { color: @ACCENT_HOVER; }
QFrame#ChannelCard[calibrated="false"] QLabel#ChannelTitle { color: @TEXT_MUTED; }
QLabel#FieldValue { color: @TEXT; font-weight: 600; }
QFrame#ChannelCard[calibrated="false"] QLabel#FieldLabel,
QFrame#ChannelCard[calibrated="false"] QLabel#FieldValue { color: @TEXT_MUTED; }
QFrame#ChannelCard QLineEdit { padding: 4px 6px; border-radius: 6px; }
QFrame#ChannelCard[calibrated="false"] QLineEdit { background: @BG; color: @TEXT_SECONDARY; }

/* ---------- Scrolling ---------- */
QScrollArea#ChannelScroll { background: transparent; border: none; }
QScrollArea#ChannelScroll > QWidget > QWidget { background: @BG; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: @BORDER_STRONG; border-radius: 3px; min-height: 30px; min-width: 30px;
}
QScrollBar::handle:hover { background: @TEXT_MUTED; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

/* ---------- Dialogs ---------- */
QMessageBox QPushButton { min-width: 80px; }
"""


def build_stylesheet():
    css = STYLESHEET
    # Longest names first so e.g. @TEXT_MUTED is not clobbered by @TEXT
    tokens = {k: v for k, v in globals().items() if k.isupper() and isinstance(v, str)}
    for name in sorted(tokens, key=len, reverse=True):
        css = css.replace("@" + name, tokens[name])
    # Scale lengths designed at 100% to the current DPI (1px hairlines stay 1px)
    return re.sub(r"(\d+)px", lambda m: f"{px(int(m.group(1))) if int(m.group(1)) > 1 else 1}px", css)


def apply_theme(app):
    app.setStyle("Fusion")
    app.setFont(QFont(FONT_FAMILY, FONT_SIZE_PT))

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(BG))
    palette.setColor(QPalette.WindowText, QColor(TEXT))
    palette.setColor(QPalette.Base, QColor(SURFACE))
    palette.setColor(QPalette.AlternateBase, QColor(SURFACE_MUTED))
    palette.setColor(QPalette.Text, QColor(TEXT))
    palette.setColor(QPalette.Button, QColor(SURFACE))
    palette.setColor(QPalette.ButtonText, QColor(TEXT))
    palette.setColor(QPalette.Highlight, QColor(ACCENT))
    palette.setColor(QPalette.HighlightedText, QColor("white"))
    palette.setColor(QPalette.PlaceholderText, QColor(TEXT_MUTED))
    palette.setColor(QPalette.ToolTipBase, QColor(SURFACE))
    palette.setColor(QPalette.ToolTipText, QColor(TEXT))
    app.setPalette(palette)

    app.setStyleSheet(build_stylesheet())


def repolish(widget):
    """Re-apply the stylesheet after a dynamic property (e.g. state) changes."""
    for w in [widget] + widget.findChildren(QWidget):
        w.style().unpolish(w)
        w.style().polish(w)
    widget.update()


def fit_to_screen(widget, width, height):
    """Resize widget to width x height, shrunk if needed to fit the screen's available area."""
    screen = QApplication.primaryScreen().availableGeometry()
    widget.resize(min(width, screen.width() - px(40)), min(height, screen.height() - px(80)))


def label(text, object_name):
    """QLabel with an object name, so the stylesheet can target it."""
    widget = QLabel(text)
    widget.setObjectName(object_name)
    return widget


def card(title=None, trailing=None):
    """White rounded card with an optional small uppercase section title. Returns (frame, layout)."""
    frame = QFrame()
    frame.setObjectName("Card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(px(16), px(12), px(16), px(16))
    layout.setSpacing(px(10))
    if title:
        header = QHBoxLayout()
        header.addWidget(label(title.upper(), "SectionTitle"))
        header.addStretch()
        if trailing:
            header.addWidget(trailing)
        layout.addLayout(header)
    return frame, layout
