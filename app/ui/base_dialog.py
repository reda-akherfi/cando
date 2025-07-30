"""
Base dialog class for the Cando application.

This module provides a base dialog class that handles dynamic sizing
based on screen dimensions for better UX across different screen sizes.
"""

from PySide6.QtWidgets import QDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QScreen


class BaseDialog(QDialog):
    """
    Base dialog class with dynamic sizing.

    Automatically sizes the dialog based on screen dimensions
    to ensure it fits comfortably on any screen size.
    """

    def __init__(self, parent=None):
        """Initialize the base dialog with dynamic sizing."""
        super().__init__(parent)
        self.setup_dynamic_sizing()

    def setup_dynamic_sizing(self):
        """Set up dynamic sizing based on screen dimensions."""
        try:
            # Get the screen geometry
            if self.parent():
                screen = self.parent().screen()
            else:
                # Fallback to primary screen
                from PySide6.QtWidgets import QApplication

                app = QApplication.instance()
                if app:
                    screen = app.primaryScreen()
                else:
                    # If no application instance, use default size
                    self.resize(500, 600)
                    return

            if not screen:
                # Fallback to default size
                self.resize(500, 600)
                return

            screen_geometry = screen.geometry()
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()

            # Handle very small screens (like mobile or small laptops)
            if screen_width < 800 or screen_height < 600:
                # Use smaller percentages for small screens
                max_width = int(screen_width * 0.95)
                max_height = int(screen_height * 0.9)
                min_width = 300
                min_height = 250
            else:
                # Use standard percentages for normal screens
                max_width = int(screen_width * 0.8)
                max_height = int(screen_height * 0.85)
                min_width = 400
                min_height = 300

            # Calculate final size with reasonable caps
            dialog_width = max(min_width, min(max_width, 800))  # Cap at 800px width
            dialog_height = max(min_height, min(max_height, 900))  # Cap at 900px height

            # Resize the dialog
            self.resize(dialog_width, dialog_height)

            # Center the dialog on screen
            self.center_on_screen(screen_geometry)

        except Exception as e:
            # Fallback to default size if anything goes wrong
            print(f"Warning: Could not set dynamic sizing: {e}")
            self.resize(500, 600)

    def center_on_screen(self, screen_geometry):
        """Center the dialog on the screen."""
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
