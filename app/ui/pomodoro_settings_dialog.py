"""
Pomodoro settings dialog for the timer widget.
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
    QCheckBox,
)
from PySide6.QtCore import Qt


class PomodoroSettingsDialog(QDialog):
    """Dialog for configuring Pomodoro timer settings."""

    def __init__(
        self,
        work_duration: int = 25,
        short_break_duration: int = 5,
        long_break_duration: int = 15,
        autostart_breaks: bool = True,
        autostart_work: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self.work_duration = work_duration
        self.short_break_duration = short_break_duration
        self.long_break_duration = long_break_duration
        self.autostart_breaks = autostart_breaks
        self.autostart_work = autostart_work
        print(
            f"PomodoroSettingsDialog initialized with: work={work_duration}m, short={short_break_duration}m, long={long_break_duration}m, autostart_breaks={autostart_breaks}, autostart_work={autostart_work}"
        )
        self.setup_ui()
        self.setup_behavior()

    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Pomodoro Settings")
        self.setModal(True)
        self.setFixedSize(350, 280)

        # Center the dialog on the parent
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Durations group
        durations_group = QGroupBox("Durations (minutes)")
        durations_layout = QGridLayout(durations_group)

        # Work duration
        durations_layout.addWidget(QLabel("Work Duration:"), 0, 0)
        self.work_duration_spin = QSpinBox()
        self.work_duration_spin.setRange(1, 100000)
        self.work_duration_spin.setValue(self.work_duration)
        durations_layout.addWidget(self.work_duration_spin, 0, 1)

        # Short break duration
        durations_layout.addWidget(QLabel("Short Break:"), 1, 0)
        self.short_break_spin = QSpinBox()
        self.short_break_spin.setRange(1, 100000)
        self.short_break_spin.setValue(self.short_break_duration)
        durations_layout.addWidget(self.short_break_spin, 1, 1)

        # Long break duration
        durations_layout.addWidget(QLabel("Long Break:"), 2, 0)
        self.long_break_spin = QSpinBox()
        self.long_break_spin.setRange(1, 100000)
        self.long_break_spin.setValue(self.long_break_duration)
        durations_layout.addWidget(self.long_break_spin, 2, 1)

        layout.addWidget(durations_group)

        # Autostart options group
        autostart_group = QGroupBox("Autostart Options")
        autostart_layout = QVBoxLayout(autostart_group)

        self.autostart_breaks_checkbox = QCheckBox("Auto-start breaks")
        self.autostart_breaks_checkbox.setChecked(self.autostart_breaks)
        autostart_layout.addWidget(self.autostart_breaks_checkbox)

        self.autostart_work_checkbox = QCheckBox("Auto-start work sessions")
        self.autostart_work_checkbox.setChecked(self.autostart_work)
        autostart_layout.addWidget(self.autostart_work_checkbox)

        layout.addWidget(autostart_group)

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
            "work_duration": self.work_duration_spin.value(),
            "short_break_duration": self.short_break_spin.value(),
            "long_break_duration": self.long_break_spin.value(),
            "autostart_breaks": self.autostart_breaks_checkbox.isChecked(),
            "autostart_work": self.autostart_work_checkbox.isChecked(),
        }
        print(f"PomodoroSettingsDialog.get_settings() returning: {settings}")
        return settings

    def set_settings(
        self,
        work_duration: int,
        short_break_duration: int,
        long_break_duration: int,
        autostart_breaks: bool,
        autostart_work: bool,
    ):
        """Set the current settings."""
        self.work_duration_spin.setValue(work_duration)
        self.short_break_spin.setValue(short_break_duration)
        self.long_break_spin.setValue(long_break_duration)
        self.autostart_breaks_checkbox.setChecked(autostart_breaks)
        self.autostart_work_checkbox.setChecked(autostart_work)
