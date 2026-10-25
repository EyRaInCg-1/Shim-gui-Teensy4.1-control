# coef_display.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PyQt5.QtGui import QFontMetrics, QFont

import theme
from theme import px


class CoefDisplayWindow(QWidget):
    def __init__(self, values, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Current Plan")

        group_count = (len(values) + 63) // 64
        card, card_layout = theme.card(f"{len(values)} values · {group_count} groups of 64")

        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("Log")
        self.text_edit.setReadOnly(True)
        card_layout.addWidget(self.text_edit)

        # Format the content: groups of 64 values, 8 values per line.
        # Non-zero values are highlighted, zeros are dimmed.
        mono = f"font-family:{theme.MONO_FAMILY}, monospace;"
        formatted = ""
        for group_idx in range(0, len(values), 64):
            group = values[group_idx:group_idx + 64]
            formatted += (
                f"<div style='margin:14px 0 6px 0; color:{theme.ACCENT_PRESSED}; font-weight:600; {mono}'>"
                f"Group {group_idx // 64 + 1}</div>"
            )
            for i in range(0, len(group), 8):
                cells = []
                for v in group[i:i + 8]:
                    color = theme.TEXT if abs(v) > 1e-6 else theme.TEXT_MUTED
                    cells.append(f"<span style='color:{color}'>{v:8.3f}</span>")
                formatted += f"<div style='{mono} white-space:pre'>{'  '.join(cells)}</div>"

        self.text_edit.setHtml(formatted)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(px(20), px(16), px(20), px(20))
        layout.setSpacing(px(12))
        layout.addWidget(theme.label(self.windowTitle(), "AppTitle"))
        layout.addWidget(card)

        # Wide enough for one row of 8 values
        fm = QFontMetrics(QFont(theme.MONO_FAMILY, theme.FONT_SIZE_PT - 1))
        theme.fit_to_screen(self, fm.horizontalAdvance("0" * 8 * 10) + px(120), px(560))

    def setWindowTitle(self, title):
        super().setWindowTitle(title)
        # Keep the in-window heading in sync (e.g. "Extra Current Plan Preview")
        heading = self.findChild(QWidget, "AppTitle")
        if heading:
            heading.setText(title)
