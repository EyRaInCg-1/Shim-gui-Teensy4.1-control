from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QApplication, QPushButton,
    QScrollArea,
)
from PyQt5.QtGui import QColor, QPainter, QFont, QFontMetrics
from PyQt5.QtCore import Qt, QTimer, QEvent
import sys
import command_utils
import theme
from theme import px, repolish

NUM_BOARDS = 8
CHANNELS_PER_BOARD = 8


class LedIndicator(QFrame):
    def __init__(self, color, diameter):
        super().__init__()
        self.color = QColor(color)
        self.diameter = diameter
        self.setFixedSize(diameter, diameter)

    def setColor(self, color):
        self.color = QColor(color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, self.diameter, self.diameter)


class ChannelWidget(QFrame):
    def __init__(self, channel_index, callback=None):
        super().__init__()
        self.channel_index = channel_index
        self.callback = callback  # Callback supplied by the parent window
        self.calibrated = None

        self.setObjectName("ChannelCard")
        self.setAttribute(Qt.WA_StyledBackground, True)

        row = channel_index // 8
        col = channel_index % 8
        self.b_num = row
        self.c_num = col

        fm = QFontMetrics(QFont(theme.FONT_FAMILY, theme.FONT_SIZE_PT))

        # Header: status LED + clickable channel name
        self.led = LedIndicator(theme.DANGER, max(8, int(fm.height() * 0.5)))
        self.label_title = theme.label(f"B{row}CH{col}", "ChannelTitle")
        self.label_title.setAttribute(Qt.WA_Hover, True)
        self.label_title.setCursor(Qt.PointingHandCursor)
        self.label_title.setToolTip("Click to read this channel")
        self.label_title.mousePressEvent = self.on_title_clicked

        header_layout = QHBoxLayout()
        header_layout.setSpacing(px(8))
        header_layout.addWidget(self.led)
        header_layout.addWidget(self.label_title)
        header_layout.addStretch()

        # Readings: name on the left, value on the right
        self.label_current = theme.label("", "FieldValue")
        self.label_gain = theme.label("", "FieldValue")
        for value in (self.label_current, self.label_gain):
            value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        fields = QGridLayout()
        fields.setHorizontalSpacing(px(12))
        fields.setVerticalSpacing(px(4))
        fields.addWidget(theme.label("Current", "FieldLabel"), 0, 0)
        fields.addWidget(self.label_current, 0, 1)
        fields.addWidget(theme.label("Gain", "FieldLabel"), 1, 0)
        fields.addWidget(self.label_gain, 1, 1)

        # Reserve room for the widest expected value so cards don't resize when data arrives
        bold = QFontMetrics(QFont(theme.FONT_FAMILY, theme.FONT_SIZE_PT, QFont.DemiBold))
        self.label_current.setMinimumWidth(bold.horizontalAdvance("-00.000 A"))

        self.input_set = QLineEdit()
        self.input_set.setPlaceholderText("Set current (A)")
        self.input_set.returnPressed.connect(self.send_current_to_serial)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(px(12), px(10), px(12), px(12))
        layout.setSpacing(px(8))
        layout.addLayout(header_layout)
        layout.addLayout(fields)
        layout.addWidget(self.input_set)

        # No data yet: show as uncalibrated
        self.reset_state()

    def on_title_clicked(self, event):
        if self.callback:
            self.callback(self.b_num, self.c_num)

    def send_current_to_serial(self):
        try:
            text = self.input_set.text().strip()
            if not text:
                return
            value = float(text)

            if self.callback:
                self.callback(self.b_num, self.c_num, value)
        except ValueError:
            print("Invalid input, must be a number")

    def set_reading(self, current, gain, calibrated):
        self.label_current.setText(f"{current:.3f} A")
        self.label_gain.setText(f"{gain:.2f}")
        self.set_calibrated(calibrated)

    def reset_state(self):
        """Clear the readings and show the channel as uncalibrated (red LED, grayed out)."""
        self.label_current.setText("-- A")
        self.label_gain.setText("--")
        self.set_calibrated(False)

    def set_calibrated(self, calibrated):
        if calibrated == self.calibrated:
            return
        self.calibrated = calibrated
        self.led.setColor(theme.SUCCESS if calibrated else theme.DANGER)
        self.setProperty("calibrated", "true" if calibrated else "false")
        repolish(self)


class CurrentDisplayWindow(QWidget):
    def __init__(self, ser):
        super().__init__()
        self.ser = ser
        self.setWindowTitle("Channel Details")

        # Auto-refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.update_all_channels)

        # Default refresh interval (ms)
        self.refresh_interval = 1000
        self.refresh_timer.setInterval(self.refresh_interval)

        # ---------- Header: title + summary on the left, controls on the right ----------
        title = theme.label("Channel Details", "AppTitle")
        self.summary_label = theme.label("", "AppSubtitle")
        self.summary_label.setTextFormat(Qt.RichText)
        self.summary_label.setWordWrap(True)  # Wraps instead of forcing the window wide


        self.update_all_button = QPushButton("Refresh All")
        self.update_all_button.setToolTip("Read all 64 channels once")
        self.update_all_button.clicked.connect(self.update_all_channels)

        self.refresh_button = QPushButton("Auto Refresh")
        self.refresh_button.setToolTip("Toggle periodic refresh (highlighted while on)")
        self.refresh_button.setCheckable(True)
        self.refresh_button.toggled.connect(self.toggle_auto_refresh)

        # Refresh interval input + unit label
        self.refresh_input = QLineEdit("1000")  # Default 1000 ms
        self.refresh_input.setAlignment(Qt.AlignRight)
        self.refresh_input.setToolTip("Auto-refresh interval, press Enter to apply")
        self.refresh_input.setFixedWidth(
            QFontMetrics(QFont(theme.FONT_FAMILY, theme.FONT_SIZE_PT)).horizontalAdvance("000000") + px(24)
        )
        self.refresh_input.returnPressed.connect(self.set_refresh_interval)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(px(8))
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.update_all_button)
        header_layout.addSpacing(px(8))
        header_layout.addWidget(self.refresh_button)
        header_layout.addWidget(self.refresh_input)
        header_layout.addWidget(theme.label("ms", "Hint"))

        # ---------- Board filter: choose which boards (rows of 8 channels) to show ----------
        self.all_boards_button = QPushButton("All")
        self.all_boards_button.setProperty("variant", "chip")
        self.all_boards_button.setCheckable(True)
        self.all_boards_button.setChecked(True)
        self.all_boards_button.clicked.connect(self.select_all_boards)

        self.board_buttons = []
        for b in range(NUM_BOARDS):
            button = QPushButton(f"B{b}")
            button.setProperty("variant", "chip")
            button.setCheckable(True)
            button.setChecked(True)
            button.setToolTip(f"Show/hide board {b}. Ctrl+click to show only this board.")
            button.clicked.connect(lambda checked, b=b: self.on_board_clicked(b, checked))
            self.board_buttons.append(button)

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(px(6))
        filter_layout.addWidget(theme.label("BOARDS", "SectionTitle"))
        filter_layout.addSpacing(px(6))
        filter_layout.addWidget(self.all_boards_button)
        filter_layout.addSpacing(px(6))
        for button in self.board_buttons:
            filter_layout.addWidget(button)
        filter_layout.addStretch()

        # Hide channels that are not calibrated (cards keep their grid position)
        self.calibrated_only_button = QPushButton("Calibrated only")
        self.calibrated_only_button.setProperty("variant", "chip")
        self.calibrated_only_button.setCheckable(True)
        self.calibrated_only_button.setToolTip("Show only channels that calibrated successfully")
        self.calibrated_only_button.toggled.connect(self.apply_board_filter)
        filter_layout.addWidget(self.calibrated_only_button)

        # ---------- Channel grid (scrollable, responsive: see relayout()) ----------
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(px(10))
        self.grid_layout.setContentsMargins(0, 0, px(4), 0)
        grid_container = QWidget()
        grid_container.setLayout(self.grid_layout)

        self.channel_widgets = [
            ChannelWidget(i, callback=self.handle_channel_input)
            for i in range(NUM_BOARDS * CHANNELS_PER_BOARD)
        ]
        # Board headings, only used when a board wraps onto several rows
        self.board_headers = []
        for b in range(NUM_BOARDS):
            header = theme.label(f"BOARD {b}", "SectionTitle")
            header.setContentsMargins(0, px(6), 0, 0)
            header.hide()
            self.board_headers.append(header)

        # Shown instead of the cards when the filters hide every channel
        self.empty_label = theme.label("No channels match the current filter.", "Hint")
        self.empty_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.empty_label.setContentsMargins(0, px(40), 0, 0)
        self.empty_label.hide()

        for widget in self.channel_widgets + self.board_headers + [self.empty_label]:
            widget.setParent(grid_container)
        self.relayout(CHANNELS_PER_BOARD)

        self.scroll_area = scroll_area = QScrollArea()
        scroll_area.setObjectName("ChannelScroll")
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(grid_container)

        # ---------- Main layout ----------
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(px(20), px(16), px(20), px(20))
        main_layout.setSpacing(px(14))
        # Title row, then the summary on its own full-width line
        top_block = QVBoxLayout()
        top_block.setSpacing(px(2))
        top_block.addLayout(header_layout)
        top_block.addWidget(self.summary_label)
        main_layout.addLayout(top_block)
        main_layout.addLayout(filter_layout)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

        self.update_summary()

        self.installEventFilter(self)
        for child in self.findChildren(QWidget):
            child.installEventFilter(self)

        # Size the window to fit all channel cards, but never larger than the screen
        self.ensurePolished()
        grid_container.ensurePolished()
        content = grid_container.sizeHint()
        margins = main_layout.contentsMargins()
        scrollbar = scroll_area.verticalScrollBar().sizeHint().width()
        width = max(content.width() + scrollbar, top_block.sizeHint().width()) + margins.left() + margins.right()
        height = (content.height() + margins.top() + margins.bottom()
                  + 2 * main_layout.spacing() + top_block.sizeHint().height()
                  + filter_layout.sizeHint().height())
        theme.fit_to_screen(self, width, height)

    # ---------- Responsive grid ----------
    def relayout(self, columns):
        """
        Place the cards `columns` per row (8, 4, 2 or 1). With 8 columns each board is
        one row; with fewer, a board wraps onto several rows under a "BOARD n" heading.
        Columns always map to the same channel numbers (e.g. 4 columns: CH0-3 / CH4-7).
        """
        self.columns = columns
        grid = self.grid_layout
        while grid.count():
            grid.takeAt(0)  # Widgets stay parented to the grid container
        for r in range(grid.rowCount()):
            grid.setRowStretch(r, 0)
        for c in range(CHANNELS_PER_BOARD):
            grid.setColumnStretch(c, 1 if c < columns else 0)

        row = 0
        for b in range(NUM_BOARDS):
            if columns < CHANNELS_PER_BOARD:
                grid.addWidget(self.board_headers[b], row, 0, 1, columns)
                row += 1
            for c in range(CHANNELS_PER_BOARD):
                widget = self.channel_widgets[b * CHANNELS_PER_BOARD + c]
                grid.addWidget(widget, row + c // columns, c % columns)
            row += CHANNELS_PER_BOARD // columns
        grid.addWidget(self.empty_label, row, 0, 1, columns)
        grid.setRowStretch(row, 1)  # Soaks up spare height when boards are hidden
        self.update_board_headers()

    def fitting_columns(self):
        """Most columns (8, 4, 2, 1) whose cards fit the current window width without scrolling sideways."""
        margins = self.layout().contentsMargins() if self.layout() else None
        available = self.width() - (margins.left() + margins.right() if margins else 0)
        available -= self.scroll_area.verticalScrollBar().sizeHint().width() + 2 * self.scroll_area.frameWidth()
        available -= self.grid_layout.contentsMargins().right()
        card = self.channel_widgets[0].minimumSizeHint().width()
        spacing = self.grid_layout.horizontalSpacing()
        for columns in (8, 4, 2):
            if columns * card + (columns - 1) * spacing <= available:
                return columns
        return 1

    def resizeEvent(self, event):
        super().resizeEvent(event)
        columns = self.fitting_columns()
        if columns != self.columns:
            self.relayout(columns)

    def update_board_headers(self, boards=None):
        boards = self.visible_boards() if boards is None else boards
        wrapped = self.columns < CHANNELS_PER_BOARD
        for b, header in enumerate(self.board_headers):
            cards = self.channel_widgets[b * CHANNELS_PER_BOARD:(b + 1) * CHANNELS_PER_BOARD]
            header.setVisible(wrapped and any(self.is_shown(w, boards) for w in cards))

    # ---------- Board filter ----------
    def on_board_clicked(self, board, checked):
        if QApplication.keyboardModifiers() & Qt.ControlModifier:
            # Ctrl+click: show only this board
            for b, button in enumerate(self.board_buttons):
                button.setChecked(b == board)
        elif not any(button.isChecked() for button in self.board_buttons):
            # Keep at least one board visible
            self.board_buttons[board].setChecked(True)
        self.apply_board_filter()

    def select_all_boards(self):
        for button in self.board_buttons:
            button.setChecked(True)
        self.apply_board_filter()

    def visible_boards(self):
        return [b for b, button in enumerate(self.board_buttons) if button.isChecked()]

    def is_shown(self, widget, boards=None):
        boards = self.visible_boards() if boards is None else boards
        if widget.b_num not in boards:
            return False
        return widget.calibrated or not self.calibrated_only_button.isChecked()

    def apply_board_filter(self):
        boards = self.visible_boards()
        for widget in self.channel_widgets:
            widget.setVisible(self.is_shown(widget, boards))
        self.all_boards_button.setChecked(len(boards) == NUM_BOARDS)
        self.update_board_headers(boards)
        self.update_empty_state(boards)
        self.update_summary()

    def update_empty_state(self, boards=None):
        boards = self.visible_boards() if boards is None else boards
        self.empty_label.setVisible(not any(self.is_shown(w, boards) for w in self.channel_widgets))

    def update_summary(self):
        boards = self.visible_boards()
        shown = [w for w in self.channel_widgets if w.b_num in boards]
        count = sum(1 for w in shown if w.calibrated)
        self.summary_label.setText(
            f"{count} of {len(shown)} channels calibrated"
            f"&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:{theme.SUCCESS}'>●</span> Calibrated"
            f"&nbsp;&nbsp;&nbsp;<span style='color:{theme.DANGER}'>●</span> Not calibrated / no data"
        )

    def show_current_data(self, b_num, c_num, Ichannel, gain, cal_Status):
        try:
            index = b_num * 8 + c_num
            if index < 0 or index >= len(self.channel_widgets):
                return

            widget = self.channel_widgets[index]
            widget.set_reading(Ichannel, gain, cal_Status)
            # Calibration state may have changed, which matters for "Calibrated only"
            widget.setVisible(self.is_shown(widget))
            self.update_board_headers()
            self.update_empty_state()
            self.update_summary()

        except Exception as e:
            print(f"Failed to update channel data: B{b_num}CH{c_num}, error: {e}")

    def update_channel_data(self, b_num, c_num):
        self.pending_b = b_num  # Remember the pending request
        self.pending_c = c_num

        info = command_utils.Ichannel_info(b_num, c_num)
        if self.ser and self.ser.is_open:
            self.ser.write(info.encode())

    def update_all_channels(self):
        if self.ser and self.ser.is_open:
            self.ser.write(b"Icurrentall\n")

    def toggle_auto_refresh(self, checked):
        # The button shows its state by color (accent when on)
        if checked:
            self.refresh_timer.start()
        else:
            self.refresh_timer.stop()

    def set_refresh_interval(self):
        try:
            interval = int(self.refresh_input.text().strip())
            if interval > 0:
                self.refresh_interval = interval
                self.refresh_timer.setInterval(self.refresh_interval)
        except ValueError:
            pass  # Ignore invalid input

    def stop_auto_refresh(self):
        if self.refresh_button.isChecked():
            self.refresh_button.setChecked(False)
            self.refresh_timer.stop()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            self.stop_auto_refresh()
        return super().eventFilter(obj, event)

    def handle_channel_input(self, b_num, c_num, current_value=None):
        if current_value is None:
            # Title clicked: query this channel only
            self.pending_b = b_num
            self.pending_c = c_num
            info = command_utils.Ichannel_info(b_num, c_num)
            if self.ser and self.ser.is_open:
                self.ser.write(info.encode())
        else:
            # Current entered: send the set-current command
            cmd = command_utils.give_one_current(b_num, c_num, current_value)
            if self.ser and self.ser.is_open:
                self.ser.write(cmd.encode())

    def reset_display(self):
        for widget in self.channel_widgets:
            widget.reset_state()
        self.apply_board_filter()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    theme.apply_theme(app)
    window = CurrentDisplayWindow(None)
    window.show()
    sys.exit(app.exec_())
