"""
Andols ECU Tuning Tool - Main Entry Point
Professional ECU binary tuning application for desktop.
"""

import sys
import os

# Ensure the application root is in the Python path
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from ui.main_window import MainWindow


def main() -> None:
    """Launch the Andols ECU Tuning Tool."""
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Andols ECU Tuning Tool")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Andols")

    # Set application-wide font
    from PyQt5.QtGui import QFont
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
