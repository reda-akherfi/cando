"""
Main entry point for the Cando application.
"""

import sys
from PySide6.QtWidgets import QApplication
from app.views.main_window import MainWindow

def main():
    """
    Main entry point for the Cando application.
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
