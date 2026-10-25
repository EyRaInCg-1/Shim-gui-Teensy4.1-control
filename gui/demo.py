# demo.py - Demo build for screenshots: no hardware needed.
# The main window looks connected and the channel details window shows all
# 64 channels calibrated, with gains between -1.60 and -1.63.
import sys
import random

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QApplication, QPushButton

import theme
from gui_window import MainWindow
from current_display import CurrentDisplayWindow, NUM_BOARDS, CHANNELS_PER_BOARD

DEMO_PORT = "COM4"
DEMO_BAUD = "115200"
random.seed(42)  # Same numbers every run
DEMO_GAINS = [-random.randint(160, 163) / 100 for _ in range(NUM_BOARDS * CHANNELS_PER_BOARD)]
# Mostly 0.000, with roughly 1 in 10 channels at ±0.001
DEMO_CURRENTS = random.choices((-0.001, 0.0, 0.001), weights=(1, 18, 1), k=NUM_BOARDS * CHANNELS_PER_BOARD)


class DemoMainWindow(MainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Teensy Serial Tool (Demo)")
        self.port_input.setText(DEMO_PORT)
        self.baud_input.setText(DEMO_BAUD)
        self.fake_connect()

    def fake_connect(self):
        """Put the window in the connected state without opening a port."""
        self.set_status("connected", f"Connected to {DEMO_PORT} @ {DEMO_BAUD}")
        for button in self.findChildren(QPushButton):
            button.setEnabled(True)
        self.connect_btn.setEnabled(False)
        self.port_input.setEnabled(False)
        self.baud_input.setEnabled(False)
        self.log(">>> E", "Initialization complete", ">>> D", "Calibration started")
        for b in range(NUM_BOARDS):
            self.log(f"Board {b}: 8/8 channels calibrated")
        self.log("Calibration finished: 64/64 channels OK")

    def log(self, *lines):
        self.console.moveCursor(QTextCursor.End)
        for line in lines:
            self.console.insertPlainText(line + "\n")

    # No serial port in demo mode: just echo commands to the log
    def send_command(self, cmd):
        self.log(f">>> {cmd.strip()}")
        if cmd.strip() == "D":
            self.log("Calibration finished: 64/64 channels OK")
        if self.current_window and cmd.strip() in ("D", "I"):
            fill_demo_data(self.current_window)

    def send_text_command(self):
        text = self.text_input.text().strip()
        if text:
            self.send_command(text)
            self.text_input.clear()

    def disconnect_serial(self):
        self.set_status("idle", "Disconnected")
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)

    def connect_serial(self):
        self.fake_connect()

    def show_current_window(self):
        if self.current_window is None:
            self.current_window = CurrentDisplayWindow(None)
            # Refresh buttons re-fill the demo values instead of querying the device
            self.current_window.update_all_channels = lambda: fill_demo_data(self.current_window)
            self.current_window.refresh_timer.timeout.disconnect()
            self.current_window.update_all_button.clicked.disconnect()
            self.current_window.update_all_button.clicked.connect(lambda: fill_demo_data(self.current_window))
        fill_demo_data(self.current_window)
        self.current_window.show()


def fill_demo_data(window):
    for i, (current, gain) in enumerate(zip(DEMO_CURRENTS, DEMO_GAINS)):
        window.show_current_data(i // CHANNELS_PER_BOARD, i % CHANNELS_PER_BOARD, current, gain, True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    theme.apply_theme(app)
    window = DemoMainWindow()
    window.show()
    QTimer.singleShot(0, window.show_current_window)  # Open the channel details window right away
    sys.exit(app.exec_())
