"""
Habit entry dialog for adding entries to habits.

This module provides a dialog for adding habit entries
with different input types based on the habit type.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QDialogButtonBox,
    QGroupBox,
    QDateEdit,
    QTimeEdit,
    QFrame,
)
from PySide6.QtCore import Qt, Signal, QTime
from PySide6.QtGui import QFont
from datetime import datetime, date, timedelta
from typing import Optional, Union
from app.models.habit import Habit, HabitEntry, HabitType


class HabitEntryDialog(QDialog):
    """Dialog for adding habit entries."""

    def __init__(self, habit: Habit, parent=None):
        super().__init__(parent)
        self.habit = habit
        self.setup_ui()
        self.center_on_screen()

    def center_on_screen(self):
        """Center the dialog on the screen."""
        screen = self.screen()
        screen_geometry = screen.geometry()

        # Calculate maximum available size (leave some margin)
        max_width = min(400, screen_geometry.width() - 100)
        max_height = min(400, screen_geometry.height() - 100)

        # Resize dialog to fit screen
        self.resize(max_width, max_height)

        # Center the dialog
        dialog_geometry = self.geometry()
        x = (screen_geometry.width() - dialog_geometry.width()) // 2
        y = (screen_geometry.height() - dialog_geometry.height()) // 2

        # Ensure dialog doesn't go off-screen
        x = max(0, min(x, screen_geometry.width() - dialog_geometry.width()))
        y = max(0, min(y, screen_geometry.height() - dialog_geometry.height()))

        self.move(x, y)

    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle(f"Add Entry - {self.habit.name}")
        self.setModal(True)
        self.resize(400, 350)
        self.setMinimumHeight(250)
        self.setMaximumHeight(500)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # Habit info
        info_group = QGroupBox("Habit Information")
        info_layout = QFormLayout(info_group)

        name_label = QLabel(self.habit.name)
        name_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        info_layout.addRow("Habit:", name_label)

        if self.habit.description:
            desc_label = QLabel(self.habit.description)
            desc_label.setWordWrap(True)
            info_layout.addRow("Description:", desc_label)

        type_label = QLabel(self.habit.habit_type.value.replace("_", " ").title())
        info_layout.addRow("Type:", type_label)

        layout.addWidget(info_group)

        # Entry details
        entry_group = QGroupBox("Entry Details")
        entry_layout = QFormLayout(entry_group)

        # Date
        self.date_edit = QDateEdit()
        self.date_edit.setDate(date.today())
        self.date_edit.setCalendarPopup(True)
        entry_layout.addRow("Date:", self.date_edit)

        # Value input based on habit type
        self.value_widget = self.create_value_widget()
        entry_layout.addRow("Value:", self.value_widget)

        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Add notes (optional)...")
        entry_layout.addRow("Notes:", self.notes_edit)

        layout.addWidget(entry_group)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def create_value_widget(self):
        """Create the appropriate value input widget based on habit type."""
        if self.habit.habit_type == HabitType.BOOLEAN:
            # Checkbox for yes/no
            widget = QCheckBox("Completed")
            widget.setChecked(True)
            return widget
        elif self.habit.habit_type == HabitType.DURATION:
            # Time input for duration
            widget = QFrame()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)

            self.hours_spin = QSpinBox()
            self.hours_spin.setRange(0, 24)
            self.hours_spin.setSuffix("h")
            layout.addWidget(self.hours_spin)

            self.minutes_spin = QSpinBox()
            self.minutes_spin.setRange(0, 59)
            self.minutes_spin.setSuffix("m")
            layout.addWidget(self.minutes_spin)

            self.seconds_spin = QSpinBox()
            self.seconds_spin.setRange(0, 59)
            self.seconds_spin.setSuffix("s")
            layout.addWidget(self.seconds_spin)

            return widget
        elif self.habit.habit_type == HabitType.UNITS:
            # Integer input for units
            widget = QSpinBox()
            widget.setRange(0, 999999)
            if self.habit.min_value is not None:
                widget.setMinimum(int(self.habit.min_value))
            if self.habit.max_value is not None:
                widget.setMaximum(int(self.habit.max_value))
            if self.habit.target_value:
                widget.setValue(int(self.habit.target_value))
            return widget
        elif self.habit.habit_type == HabitType.REAL_NUMBER:
            # Float input for real numbers - use QLineEdit for better decimal input
            widget = QLineEdit()
            widget.setPlaceholderText("Enter decimal value (e.g., 0.75)")
            # Always start with 0.0 for new entries, not the target value
            widget.setText("0.0")
            return widget
        elif self.habit.habit_type == HabitType.RATING:
            # Rating scale input
            widget = QComboBox()
            widget.addItems([str(i) for i in range(1, self.habit.rating_scale + 1)])
            widget.setCurrentText(
                str(self.habit.rating_scale // 2)
            )  # Default to middle
            return widget
        elif self.habit.habit_type == HabitType.COUNT:
            # Integer input for count
            widget = QSpinBox()
            widget.setRange(0, 999999)
            if self.habit.min_value is not None:
                widget.setMinimum(int(self.habit.min_value))
            if self.habit.max_value is not None:
                widget.setMaximum(int(self.habit.max_value))
            widget.setValue(1)  # Default to 1 for count
            return widget
        else:
            # Fallback to text input
            widget = QLineEdit()
            widget.setPlaceholderText("Enter value...")
            return widget

    def get_value(self) -> Union[bool, int, float, str]:
        """Get the value from the appropriate widget."""
        if self.habit.habit_type == HabitType.BOOLEAN:
            return self.value_widget.isChecked()
        elif self.habit.habit_type == HabitType.DURATION:
            # Convert to seconds
            hours = self.hours_spin.value()
            minutes = self.minutes_spin.value()
            seconds = self.seconds_spin.value()
            return hours * 3600 + minutes * 60 + seconds
        elif self.habit.habit_type == HabitType.UNITS:
            return self.value_widget.value()
        elif self.habit.habit_type == HabitType.REAL_NUMBER:
            try:
                return float(self.value_widget.text())
            except ValueError:
                # If invalid input, return 0.0 as fallback
                return 0.0
        elif self.habit.habit_type == HabitType.RATING:
            return int(self.value_widget.currentText())
        elif self.habit.habit_type == HabitType.COUNT:
            return self.value_widget.value()
        else:
            return self.value_widget.text()

    def get_entry(self) -> Optional[HabitEntry]:
        """Get the habit entry from the dialog."""
        value = self.get_value()
        print(f"DEBUG: get_entry called with value: {value} (type: {type(value)})")

        # Validate value
        if self.habit.habit_type == HabitType.BOOLEAN:
            # Boolean is always valid
            pass
        elif self.habit.habit_type == HabitType.DURATION:
            if value <= 0:
                print("DEBUG: Duration validation failed - value <= 0")
                return None  # Duration must be positive
        elif self.habit.habit_type == HabitType.UNITS:
            if value < 0:
                print("DEBUG: Units validation failed - value < 0")
                return None  # Units must be non-negative
        elif self.habit.habit_type == HabitType.REAL_NUMBER:
            # Real numbers can be negative unless constrained
            # Check min/max constraints if set
            if self.habit.min_value is not None and value < self.habit.min_value:
                print(
                    f"DEBUG: Real number validation failed - value {value} < min {self.habit.min_value}"
                )
                return None  # Value below minimum
            if (
                self.habit.max_value is not None
                and self.habit.max_value > 0
                and value > self.habit.max_value
            ):
                print(
                    f"DEBUG: Real number validation failed - value {value} > max {self.habit.max_value}"
                )
                return None  # Value above maximum
        elif self.habit.habit_type == HabitType.RATING:
            if not (1 <= value <= self.habit.rating_scale):
                print(
                    f"DEBUG: Rating validation failed - value {value} not in range 1-{self.habit.rating_scale}"
                )
                return None  # Rating must be within scale
        elif self.habit.habit_type == HabitType.COUNT:
            if value < 0:
                print("DEBUG: Count validation failed - value < 0")
                return None  # Count must be non-negative

        print(f"DEBUG: Validation passed, creating entry with value: {value}")
        return HabitEntry(
            id=0,  # Will be set by database
            habit_id=self.habit.id,
            date=self.date_edit.date().toPython(),
            value=value,
            notes=self.notes_edit.toPlainText().strip() or None,
        )
