"""
ALLICE — AI Software Engineering Assistant
Entry point.

Requirements:
  pip install PySide6 psutil pygments requests

Run:
  python main.py
"""

import sys
import os

# Make sure imports resolve from project root
sys.path.insert(0, os.path.dirname(__file__))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from ui.app import AlliceWindow


def load_theme(app: QApplication) -> None:
    theme_path = os.path.join(os.path.dirname(__file__), "styles", "theme.qss")
    try:
        with open(theme_path, "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"[ALLICE] Warning: theme.qss not found at {theme_path}")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ALLICE")
    app.setOrganizationName("ALLICE")

    # Set application-wide font
    font = QFont("Segoe UI", 12)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)

    load_theme(app)

    window = AlliceWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
