# main.py
import sys
from PyQt5.QtWidgets import QApplication
from gui_window import MainWindow
import theme

if __name__ == '__main__':
    app = QApplication(sys.argv)
    theme.apply_theme(app)  # Must come before creating windows (they size themselves from the styled content)
    window = MainWindow()  # Sizes itself to its content and the screen
    window.show()
    sys.exit(app.exec_())
