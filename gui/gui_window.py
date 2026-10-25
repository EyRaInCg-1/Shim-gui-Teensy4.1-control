import serial
import threading
import re
from serial.tools import list_ports
import struct
import time

from PyQt5.QtCore import pyqtSignal, QObject, QEvent
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
    QLineEdit,
    QMessageBox,
    QFileDialog,
    QDialog,
    QGridLayout,
)

from current_display import CurrentDisplayWindow
import theme
from theme import px, repolish, fit_to_screen
from coef_display import CoefDisplayWindow

from command_utils import extra_current_plan, extra_plan_index, give_one_current
from command_utils import apply_next_extra_group, reset_extra_plan_index
from command_utils import load_extra_plan_from_file
from command_utils import extra_plan_index, reset_extra_plan_index, apply_next_extra_group
from PyQt5.QtGui import QFont


global coefStore, coef_num
coefStore = [0.0] * 50000
coef_num = 40


class SerialReader(QObject):
    data_received = pyqtSignal(str)

    def __init__(self, serial_port):
        super().__init__()
        self.ser = serial_port
        self._running = True
        self.thread = threading.Thread(target=self.read_loop)
        self.thread.daemon = True
        self.thread.start()

    def read_loop(self):
        while self._running:
            if self.ser.in_waiting:
                try:
                    raw = self.ser.readline()
                    line = raw.decode("utf-8", errors="ignore").strip()
                    if line:
                        self.data_received.emit(line)
                except Exception as e:
                    print("Read error:", e)


    def stop(self):
        self._running = False


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Teensy Serial Tool")
        self.ser = None
        self.reader = None
        self.in_icurrentall_mode = False
        self.icurrentall_buffer = []

        # Widgets
        self.port_input = QLineEdit("COM4")
        self.baud_input = QLineEdit("115200")

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setProperty("variant", "primary")
        self.disconnect_btn = QPushButton("Disconnect")
        self.connect_btn.clicked.connect(self.connect_serial)
        self.disconnect_btn.clicked.connect(self.disconnect_serial)
        self.disconnect_btn.setEnabled(False)

        self.status_label = theme.label("", "StatusPill")


        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type a command and press Enter")
        self.text_input.returnPressed.connect(self.send_text_command)

        self.send_text_btn = QPushButton("Send")
        self.send_text_btn.clicked.connect(self.send_text_command)
        # Always enabled: sending while disconnected just logs a hint

        self.btn_setup = QPushButton("Initialize")
        self.btn_setup.clicked.connect(lambda: self.send_command("E\n"))
        self.btn_setup.setEnabled(False)

        self.btn_calibrate = QPushButton("Calibrate")
        self.btn_calibrate.clicked.connect(lambda: self.send_command("D\n"))
        self.btn_calibrate.setEnabled(False)

        self.btn_show_current = QPushButton("Show Current")
        self.btn_show_current.clicked.connect(lambda: self.send_command("I\n"))
        self.btn_show_current.setEnabled(False)

        self.btn_zeroall = QPushButton("Zero All Currents")
        self.btn_zeroall.clicked.connect(lambda: self.send_command("Z\n"))
        self.btn_zeroall.setEnabled(False)

        self.btn_nextblock = QPushButton("Next Current Block")
        self.btn_nextblock.clicked.connect(lambda: self.send_command("T\n"))
        self.btn_nextblock.setEnabled(False)

        self.btn_firstblock = QPushButton("First Current Block")
        self.btn_firstblock.clicked.connect(lambda: self.send_command("M\n"))
        self.btn_firstblock.setEnabled(False)

        self.console = QTextEdit()
        self.console.setObjectName("Log")
        self.console.setReadOnly(True)
        self.console.setPlaceholderText("Serial output will appear here.")

        # Path display for the loaded TXT file
        self.load_path_display = QLineEdit()
        self.load_path_display.setPlaceholderText("Select a TXT file to load")
        self.load_path_display.setReadOnly(True)

        self.btn_load_txt = QPushButton("Load")
        self.btn_load_txt.clicked.connect(self.load_txt_file)
        self.btn_load_txt.setEnabled(False)

        self.btn_show_values = QPushButton("View Current Plan")
        self.btn_show_values.clicked.connect(lambda: self.show_all_coefStore())
        self.btn_show_values.setEnabled(False)


        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setProperty("variant", "ghost")
        self.btn_clear.clicked.connect(self.console.clear)
        self.btn_clear.setEnabled(False)
        self.current_window = None  # Reference to the channel details window

        self.btn_showallcurrent = QPushButton("Open Channel Details")
        self.btn_showallcurrent.setProperty("variant", "primary")
        self.btn_showallcurrent.clicked.connect(self.show_current_window)
        self.btn_showallcurrent.clicked.connect(lambda: self.send_command("I\n"))
        # Always enabled: the panel can be opened without a device connected

        self.btn_upload_coef = QPushButton("Upload Current Plan")
        self.btn_upload_coef.clicked.connect(self.upload_coef_to_teensy)
        self.btn_upload_coef.setEnabled(False)  # Disabled until connected

        self.btn_next_extra_group = QPushButton("Next Group")
        self.btn_next_extra_group.clicked.connect(self.apply_next_extra_group_gui)
        self.btn_next_extra_group.setEnabled(False)  # Disabled until connected

        self.btn_reset_extra = QPushButton("Reset Group")
        self.btn_reset_extra.clicked.connect(self.reset_extra_plan_gui)
        self.btn_reset_extra.setEnabled(False)


        self.btn_load_extra_txt = QPushButton("Load Extra Plan")
        self.btn_load_extra_txt.clicked.connect(self.load_extra_txt_gui)
        self.btn_load_extra_txt.setEnabled(False)

        self.btn_preview_extra = QPushButton("Preview Extra Plan")
        self.btn_preview_extra.clicked.connect(self.preview_extra_plan_gui)
        self.btn_preview_extra.setEnabled(False)

        self.group_index = 0
        self.group_label = theme.label("Group 0", "Badge")

        self.btn_prev_extra_group = QPushButton("Previous Group")
        self.btn_prev_extra_group.clicked.connect(self.apply_prev_extra_group_gui)
        self.btn_prev_extra_group.setEnabled(False)


        # (Not shown in the layout: btn_nextblock, btn_firstblock,
        #  load_path_display / btn_load_txt, btn_upload_coef, btn_show_values)

        # ---------- Header ----------
        header = QVBoxLayout()
        header.setSpacing(px(2))
        header.addWidget(theme.label("Active Shimming Control", "AppTitle"))
        header.addWidget(theme.label("64-channel shim current driver · Teensy 4.1", "AppSubtitle"))

        # ---------- Left column: control cards ----------
        # Connection
        connection_card, connection = theme.card("Connection")
        port_row = QGridLayout()
        port_row.setHorizontalSpacing(px(8))
        port_row.setVerticalSpacing(px(4))
        port_row.setColumnStretch(0, 1)
        port_row.setColumnStretch(1, 1)
        self.port_label = theme.label("Port", "FieldLabel")
        self.baud_label = theme.label("Baud rate", "FieldLabel")
        port_row.addWidget(self.port_label, 0, 0)
        port_row.addWidget(self.baud_label, 0, 1)
        port_row.addWidget(self.port_input, 1, 0)
        port_row.addWidget(self.baud_input, 1, 1)
        connection.addLayout(port_row)
        connection.addLayout(button_grid([self.connect_btn, self.disconnect_btn]))
        connection.addWidget(self.status_label)

        # Device commands
        device_card, device = theme.card("Device")
        device.addLayout(button_grid(
            [self.btn_setup, self.btn_calibrate],
            [self.btn_show_current, self.btn_zeroall],
        ))

        # Current plan (extra plan groups)
        plan_card, plan = theme.card("Current plan", trailing=self.group_label)
        plan.addLayout(button_grid(
            [self.btn_prev_extra_group, self.btn_next_extra_group],
            [self.btn_load_extra_txt, self.btn_preview_extra],
            [self.btn_reset_extra],
        ))

        left_layout = QVBoxLayout()
        left_layout.setSpacing(px(12))
        left_layout.addWidget(connection_card)
        left_layout.addWidget(device_card)
        left_layout.addWidget(plan_card)
        left_layout.addStretch()
        left_layout.addWidget(self.btn_showallcurrent)

        # ---------- Right column: serial log ----------
        log_card, log = theme.card("Serial log", trailing=self.btn_clear)
        log.addWidget(self.console)
        command_row = QHBoxLayout()
        command_row.setSpacing(px(8))
        command_row.addWidget(self.text_input, stretch=1)
        command_row.addWidget(self.send_text_btn)
        log.addLayout(command_row)

        # ---------- Main layout ----------
        body = QHBoxLayout()
        body.setSpacing(px(12))
        body.addLayout(left_layout, stretch=0)
        body.addWidget(log_card, stretch=1)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(px(20), px(16), px(20), px(20))
        main_layout.setSpacing(px(14))
        main_layout.addLayout(header)
        main_layout.addLayout(body)
        self.setLayout(main_layout)

        self.installEventFilter(self)
        for child in self.findChildren(QWidget):
            child.installEventFilter(self)

        # Size the window from its content: controls at their natural width,
        # plus room for ~56 characters of log output
        self.ensurePolished()
        margins = main_layout.contentsMargins()
        log_width = self.console.fontMetrics().averageCharWidth() * 56
        width = left_layout.sizeHint().width() + body.spacing() + log_width + margins.left() + margins.right()
        height = self.sizeHint().height()
        fit_to_screen(self, width, height)

        auto_port = find_teensy_port()
        if auto_port:
            self.port_input.setText(auto_port)
            self.set_status("detected", f"Teensy detected on {auto_port}")
        else:
            self.set_status("idle", "No Teensy found, enter the port manually")

    def set_status(self, state, text):
        """state: 'idle' (gray), 'detected' (accent) or 'connected' (green)."""
        self.status_label.setText(f"●  {text}")
        self.status_label.setProperty("state", state)
        repolish(self.status_label)

    def connect_serial(self):
        port = self.port_input.text().strip()
        baud = self.baud_input.text().strip()

        if not port or not baud.isdigit():
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid port and baud rate.")
            return

        try:
            self.ser = serial.Serial(port, int(baud), timeout=1)
            self.set_status("connected", f"Connected to {port} @ {baud}")

            self.reader = SerialReader(self.ser)
            self.reader.data_received.connect(self.handle_serial_data)

            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.port_input.setEnabled(False)
            self.baud_input.setEnabled(False)
            self.btn_clear.setEnabled(True)
            self.btn_calibrate.setEnabled(True)
            self.btn_show_current.setEnabled(True)
            self.btn_zeroall.setEnabled(True)
            self.btn_nextblock.setEnabled(True)
            self.btn_firstblock.setEnabled(True)
            self.btn_setup.setEnabled(True)
            self.load_path_display.setEnabled(True)
            self.btn_load_txt.setEnabled(True)
            self.btn_show_values.setEnabled(True)
            self.btn_upload_coef.setEnabled(True)
            if self.current_window:
                self.current_window.ser = self.ser
            self.btn_next_extra_group.setEnabled(True)
            self.btn_reset_extra.setEnabled(True)
            self.btn_load_extra_txt.setEnabled(True)
            self.btn_preview_extra.setEnabled(True)
            self.btn_prev_extra_group.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Connection Failed", f"Unable to open serial port:\n{describe_serial_error(e)}")

    def disconnect_serial(self):
        if self.reader:
            self.reader.stop()
            self.reader = None
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.ser = None


        self.set_status("idle", "Disconnected")


        self.port_input.setEnabled(True)
        self.baud_input.setEnabled(True)
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.btn_clear.setEnabled(False)
        self.btn_calibrate.setEnabled(False)
        self.btn_show_current.setEnabled(False)
        self.btn_zeroall.setEnabled(False)
        self.btn_nextblock.setEnabled(False)
        self.btn_firstblock.setEnabled(False)
        self.btn_setup.setEnabled(False)
        if self.current_window:
            self.current_window.stop_auto_refresh()
            self.current_window.ser = None
            self.current_window.reset_display()  # Disconnected: all channels back to uncalibrated
        self.load_path_display.setEnabled(False)
        self.btn_load_txt.setEnabled(False)
        self.btn_show_values.setEnabled(False)
        self.btn_upload_coef.setEnabled(False)
        self.btn_next_extra_group.setEnabled(False)
        self.btn_reset_extra.setEnabled(False)
        self.btn_load_extra_txt.setEnabled(False)
        self.btn_preview_extra.setEnabled(False)
        self.btn_prev_extra_group.setEnabled(False)

    def send_command(self, cmd):
        if self.ser and self.ser.is_open:
            full_cmd = cmd.strip() + "\n"  # Make sure the command ends with a newline
            self.ser.write(full_cmd.encode())

            # Insert the log line precisely (avoids extra blank lines)
            self.console.moveCursor(QTextCursor.End)
            self.console.insertPlainText(f">>> {cmd.strip()}\n")

    def send_text_command(self):
        text = self.text_input.text().strip()
        if not text:
            return
        self.console.moveCursor(QTextCursor.End)
        if not (self.ser and self.ser.is_open):
            # Keep the typed text so it can be sent after connecting
            self.console.insertPlainText(f"Not connected, command not sent: {text}\n")
            return
        self.ser.write((text + "\n").encode())
        self.console.insertPlainText(f">>> {text}\n")
        self.text_input.clear()

    def handle_serial_data(self, data):
        data = data.strip()
        self.console.moveCursor(QTextCursor.End)
        self.console.insertPlainText(data + "\n")

        # -- Enter batch mode --
        if data == "Icurrentall":
            self.in_icurrentall_mode = True
            self.icurrentall_buffer = []
            return

        # -- Exit batch mode --
        if data == "IcurrentallEnd":
            if self.in_icurrentall_mode:
                self.process_icurrentall_buffer()
                self.in_icurrentall_mode = False
            return

        # -- In batch mode, buffer every line --
        if self.in_icurrentall_mode:
            self.icurrentall_buffer.append(data)
            return

        # -- Single-channel Icurrent data (e.g. "Icurrent 3 6 1.23 1.00 T") --
        if data.startswith("Icurrent"):
            parts = data.strip().split()
            if len(parts) == 6:
                try:
                    b = int(parts[1])
                    c = int(parts[2])
                    current = float(parts[3])
                    gain = float(parts[4])
                    cal_Status = parts[5].upper() == "T"

                    if self.current_window:
                        self.current_window.show_current_data(
                            b, c, current, gain, cal_Status
                        )
                except Exception as e:
                    print(f"Failed to parse Icurrent line: {e}")
            return

        # Other messages: ignored

    def closeEvent(self, event):
        self.disconnect_serial()
        event.accept()

    def show_current_window(self):
        if self.current_window is None:
            self.current_window = CurrentDisplayWindow(self.ser)
        else:
            self.current_window.stop_auto_refresh()
        self.current_window.ser = self.ser  # Keep the panel on the current connection
        self.current_window.reset_display()
        self.current_window.show()

    def process_icurrentall_buffer(self):
        for line in self.icurrentall_buffer:
            parts = line.strip().split()
            if len(parts) == 5:
                try:
                    b = int(parts[0])
                    c = int(parts[1])
                    current = float(parts[2])
                    gain = float(parts[3])
                    cal_Status = parts[4].upper() == "T"

                    if self.current_window:
                        self.current_window.show_current_data(
                            b, c, current, gain, cal_Status
                        )
                except Exception as e:
                    print(f"Failed to parse Icurrentall line: {line}, error: {e}")

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if self.current_window:
                self.current_window.stop_auto_refresh()
        return super().eventFilter(obj, event)

    def load_txt_file(self):
        global coefStore, coef_num
        coefStore = [0.0] * 50000
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select TXT File", "", "Text Files (*.txt)"
        )
        if not file_path:
            return

        self.load_path_display.setText(file_path)

        try:
            with open(file_path, "r") as f:
                values = []
                for line in f:
                    parts = re.split(r'[,\s]+', line.strip())  # Accepts commas, spaces and tabs
                    for val in parts:
                        if val:  # Skip empty strings
                            values.append(float(val))


            if len(values) > 50000:
                QMessageBox.warning(
                    self, "Too Much Data", "The file contains more than 50000 values; only the first 50000 will be loaded."
                )
                values = values[:50000]

            coefStore[: len(values)] = values
            QMessageBox.information(self, "Success", f"Loaded {len(values)} coefficient values.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file: {e}")

        coefStore[:len(values)] = values
        coef_num = len(values)  # Record the actual count


    def show_all_coefStore(self):
        global coefStore, coef_num
        self.show_all_values_dialog(coefStore[:coef_num])


    def show_all_values_dialog(self, values):
        self.coef_window = CoefDisplayWindow(values)
        self.coef_window.show()

    def upload_coef_to_teensy(self):
        global coefStore, coef_num

        if not self.ser or not self.ser.is_open:
            QMessageBox.warning(self, "Not Connected", "Please connect to the serial device first.")
            return

        try:
            # 1. Tell the Teensy to enter receive mode
            self.ser.write(b"uploadcoef\n")
            self.console.append(">>> uploadcoef")

            # 2. Wait for the Teensy to get ready
            time.sleep(0.1)

            # 3. Pack and send the float array (binary)
            float_data = struct.pack(f"<{coef_num}f", *coefStore[:coef_num])
            self.ser.write(float_data)

            self.console.append(f">>> Sent {coef_num} floats, {len(float_data)} bytes total")
            QMessageBox.information(self, "Upload Complete", f"Uploaded {coef_num} coefficient values.")

        except Exception as e:
            QMessageBox.critical(self, "Upload Failed", f"An error occurred during transfer:\n{describe_serial_error(e)}")

    def apply_next_extra_group_gui(self):
        try:
            apply_next_extra_group(
                self.ser,
                console=self.console,
                channel_widgets=self.current_window.channel_widgets if self.current_window else None
            )
            if self.ser and self.ser.is_open:
                self.ser.write(b"Icurrentall\n")
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))

    def reset_extra_plan_gui(self):
        try:

            reset_extra_plan_index(
                ser=self.ser,
                channel_widgets=self.current_window.channel_widgets if self.current_window else None
            )
            self.group_index = 0
            self.group_label.setText("Group 0")
            self.console.append(">>> Group reset and all currents zeroed")
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))


    def load_extra_txt_gui(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Extra Plan TXT File", "", "Text Files (*.txt)"
        )
        if not file_path:
            return

        try:
            count = load_extra_plan_from_file(file_path)
            self.reset_extra_plan_gui()
            QMessageBox.information(
                self,
                "Load Successful",
                f"Loaded {count} extra values ({count // 64} groups)."
            )

        except Exception as e:
            QMessageBox.critical(self, "Load Failed", str(e))

    def preview_extra_plan_gui(self):
        from command_utils import extra_current_plan

        # If empty, show 64 zeros
        values = extra_current_plan if extra_current_plan else [0.0] * 64

        self.extra_preview_window = CoefDisplayWindow(values)
        self.extra_preview_window.setWindowTitle("Extra Current Plan Preview")
        self.extra_preview_window.show()

    def apply_next_extra_group_gui(self):
        try:
            apply_next_extra_group(
                self.ser,
                console=self.console,
                channel_widgets=self.current_window.channel_widgets if self.current_window else None
            )
            if self.ser and self.ser.is_open:
                self.ser.write(b"Icurrentall\n")
            self.group_index += 1
            self.group_label.setText(f"Group {self.group_index}")
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))

    def apply_prev_extra_group_gui(self):
        from command_utils import apply_prev_extra_group
        try:
            apply_prev_extra_group(
                self.ser,
                console=self.console,
                channel_widgets=self.current_window.channel_widgets if self.current_window else None
            )
            if self.ser and self.ser.is_open:
                self.ser.write(b"Icurrentall\n")
            self.group_index = max(0, self.group_index - 1)
            self.group_label.setText(f"Group {self.group_index}")
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))


def button_grid(*rows):
    """Two equal-width columns of buttons; a row with a single button spans both columns."""
    grid = QGridLayout()
    grid.setSpacing(px(8))
    grid.setColumnStretch(0, 1)
    grid.setColumnStretch(1, 1)
    for r, buttons in enumerate(rows):
        if len(buttons) == 1:
            grid.addWidget(buttons[0], r, 0, 1, 2)
        else:
            for c, button in enumerate(buttons):
                grid.addWidget(button, r, c)
    return grid


# English descriptions for common Windows serial error codes
WIN_SERIAL_ERRORS = {
    2: "Port not found. Check that the device is connected and the port name is correct.",
    5: "Access denied. The port may already be in use by another program (e.g. a serial monitor).",
    22: "The device does not recognize the command.",
    31: "The device attached to the system is not functioning.",
    121: "The device did not respond (semaphore timeout).",
    433: "The device does not exist.",
    1167: "The device is not connected.",
}


def describe_serial_error(e):
    """
    pyserial embeds the Windows error message, which is localized to the OS
    language (e.g. "FileNotFoundError(2, '<localized text>', None, 2)").
    Replace it with an English description based on the Windows error code.
    """
    msg = str(e)
    match = re.search(r"\w+\(-?\d+, '.*?', None, (-?\d+)\)", msg)
    if match:
        code = int(match.group(1))
        desc = WIN_SERIAL_ERRORS.get(code, "Windows system error.")
        msg = msg.replace(match.group(0), f"{desc} (WinError {code})")
    return msg


def find_teensy_port():
    ports = list_ports.comports()
    for port in ports:
        # Print port.description / port.hwid / port.vid etc. here for debugging
        if "Teensy" in port.description or (port.vid == 0x16C0 and port.pid == 0x0483):
            return port.device  # Port name, e.g. COM4
    return None
