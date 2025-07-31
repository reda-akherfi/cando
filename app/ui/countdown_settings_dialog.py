"""
Countdown settings dialog for the timer widget.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QPushButton,
    QGroupBox,
    QGridLayout,
)
from PySide6.QtCore import Qt


class CountdownSettingsDialog(QDialog):
    """Dialog for configuring countdown timer settings."""

    def __init__(self, minutes: int = 30, seconds: int = 0, parent=None):
        super().__init__(parent)
        self.minutes = minutes
        self.seconds = seconds
        print(f"CountdownSettingsDialog initialized with: {minutes}m {seconds}s")
        self.setup_ui()
        self.setup_behavior()

    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Countdown Settings")
        self.setModal(True)
        self.setFixedSize(300, 150)

        # Center the dialog on the parent
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Settings group
        settings_group = QGroupBox("Duration")
        settings_layout = QGridLayout(settings_group)

        # Minutes
        settings_layout.addWidget(QLabel("Minutes:"), 0, 0)
        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(0, 100000)
        self.minutes_spin.setValue(self.minutes)
        settings_layout.addWidget(self.minutes_spin, 0, 1)

        # Seconds
        settings_layout.addWidget(QLabel("Seconds:"), 1, 0)
        self.seconds_spin = QSpinBox()
        self.seconds_spin.setRange(0, 100000)
        self.seconds_spin.setValue(self.seconds)
        settings_layout.addWidget(self.seconds_spin, 1, 1)

        layout.addWidget(settings_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)

        layout.addLayout(button_layout)

    def setup_behavior(self):
        """Set up dialog behavior."""
        # Set focus to OK button
        self.ok_button.setDefault(True)
        self.ok_button.setFocus()

    def get_settings(self):
        """Get the current settings."""
        settings = {
            "minutes": self.minutes_spin.value(),
            "seconds": self.seconds_spin.value(),
        }
        print(f"CountdownSettingsDialog.get_settings() returning: {settings}")
        return settings

    def set_settings(self, minutes: int, seconds: int):
        """Set the current settings."""
        self.minutes_spin.setValue(minutes)
        self.seconds_spin.setValue(seconds)
