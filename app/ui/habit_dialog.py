"""
Habit dialog for creating and editing habits.

This module provides a dialog for creating and editing habits
with support for all habit types and configurations.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QFormLayout,
    QDialogButtonBox,
    QColorDialog,
    QGroupBox,
    QGridLayout,
    QFrame,
    QScrollArea,
    QWidget,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from datetime import datetime
from typing import Optional, List
from app.models.habit import Habit, HabitType, HabitFrequency


class HabitDialog(QDialog):
    """Dialog for creating and editing habits."""

    def __init__(self, habit: Optional[Habit] = None, parent=None):
        super().__init__(parent)
        self.habit = habit
        self.is_editing = habit is not None
        self.setup_ui()
        self.load_habit_data()
        self.center_on_screen()

    def center_on_screen(self):
        """Center the dialog on the screen."""
        screen = self.screen()
        screen_geometry = screen.geometry()

        # Calculate maximum available size (leave some margin)
        max_width = min(500, screen_geometry.width() - 100)
        max_height = min(600, screen_geometry.height() - 100)

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
        self.setWindowTitle("Edit Habit" if self.is_editing else "Create Habit")
        self.setModal(True)
        self.resize(500, 600)
        self.setMinimumHeight(300)
        self.setMaximumHeight(800)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Create scroll area for form content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setMinimumHeight(200)

        # Create widget to hold form content
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(8)
        form_layout.setContentsMargins(4, 4, 4, 4)

        # Basic information
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter habit name...")
        basic_layout.addRow("Name:", self.name_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(60)
        self.description_edit.setPlaceholderText("Enter description (optional)...")
        basic_layout.addRow("Description:", self.description_edit)

        form_layout.addWidget(basic_group)

        # Habit type and configuration
        config_group = QGroupBox("Habit Configuration")
        config_layout = QFormLayout(config_group)

        # Habit type
        self.habit_type_combo = QComboBox()
        self.habit_type_combo.addItems(
            [
                "Boolean (Yes/No)",
                "Duration (Time-based)",
                "Units (Integer)",
                "Real Number (Float)",
                "Rating (1-10 scale)",
                "Count (Simple counter)",
            ]
        )
        self.habit_type_combo.currentIndexChanged.connect(self.on_habit_type_changed)
        config_layout.addRow("Type:", self.habit_type_combo)

        # Frequency
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["Daily", "Weekly", "Monthly", "Custom"])
        self.frequency_combo.currentIndexChanged.connect(self.on_frequency_changed)
        config_layout.addRow("Frequency:", self.frequency_combo)

        # Custom interval
        self.custom_interval_spin = QSpinBox()
        self.custom_interval_spin.setRange(1, 365)
        self.custom_interval_spin.setSuffix(" days")
        self.custom_interval_spin.setVisible(False)
        config_layout.addRow("Custom interval:", self.custom_interval_spin)

        form_layout.addWidget(config_group)

        # Type-specific settings
        self.type_settings_group = QGroupBox("Type Settings")
        self.type_settings_layout = QFormLayout(self.type_settings_group)
        form_layout.addWidget(self.type_settings_group)

        # Target and unit settings
        target_group = QGroupBox("Target & Unit")
        target_layout = QFormLayout(target_group)

        self.target_value_spin = QDoubleSpinBox()
        self.target_value_spin.setRange(0, 999999)
        self.target_value_spin.setDecimals(4)  # Allow up to 4 decimal places
        self.target_value_spin.setSingleStep(0.01)  # Step by 0.01 for easier navigation
        target_layout.addRow("Target value:", self.target_value_spin)

        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("e.g., steps, minutes, kg")
        target_layout.addRow("Unit:", self.unit_edit)

        form_layout.addWidget(target_group)

        # Value range settings
        range_group = QGroupBox("Value Range (Optional)")
        range_layout = QFormLayout(range_group)

        self.min_value_spin = QDoubleSpinBox()
        self.min_value_spin.setRange(-999999, 999999)
        self.min_value_spin.setDecimals(4)  # Allow up to 4 decimal places
        self.min_value_spin.setSingleStep(0.01)  # Step by 0.01 for easier navigation
        range_layout.addRow("Minimum value:", self.min_value_spin)

        self.max_value_spin = QDoubleSpinBox()
        self.max_value_spin.setRange(-999999, 999999)
        self.max_value_spin.setDecimals(4)  # Allow up to 4 decimal places
        self.max_value_spin.setSingleStep(0.01)  # Step by 0.01 for easier navigation
        range_layout.addRow("Maximum value:", self.max_value_spin)

        form_layout.addWidget(range_group)

        # Color and tags
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)

        # Color picker
        color_layout = QHBoxLayout()
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(24, 24)
        self.color_preview.setStyleSheet(
            "background-color: #007bff; border: 1px solid #ccc; border-radius: 3px;"
        )
        color_layout.addWidget(self.color_preview)

        self.color_btn = QPushButton("Choose Color")
        self.color_btn.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch()

        appearance_layout.addRow("Color:", color_layout)

        # Tags
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Enter tags separated by commas...")
        appearance_layout.addRow("Tags:", self.tags_edit)

        form_layout.addWidget(appearance_group)

        # Status
        status_group = QGroupBox("Status")
        status_layout = QFormLayout(status_group)

        self.active_check = QCheckBox("Active")
        self.active_check.setChecked(True)
        status_layout.addRow("", self.active_check)

        form_layout.addWidget(status_group)

        # Add stretch to push content to top
        form_layout.addStretch()

        # Set the form widget as the scroll area's widget
        scroll_area.setWidget(form_widget)
        main_layout.addWidget(scroll_area, 1)  # Give scroll area stretch factor

        # Buttons - always visible at bottom
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box, 0)  # No stretch for buttons

        # Initialize with default values
        self.current_color = "#007bff"
        self.on_habit_type_changed(0)

    def load_habit_data(self):
        """Load existing habit data if editing."""
        if not self.habit:
            return

        self.name_edit.setText(self.habit.name)
        if self.habit.description:
            self.description_edit.setPlainText(self.habit.description)

        # Set habit type
        type_index_map = {
            HabitType.BOOLEAN: 0,
            HabitType.DURATION: 1,
            HabitType.UNITS: 2,
            HabitType.REAL_NUMBER: 3,
            HabitType.RATING: 4,
            HabitType.COUNT: 5,
        }
        self.habit_type_combo.setCurrentIndex(
            type_index_map.get(self.habit.habit_type, 0)
        )

        # Set frequency
        freq_index_map = {
            HabitFrequency.DAILY: 0,
            HabitFrequency.WEEKLY: 1,
            HabitFrequency.MONTHLY: 2,
            HabitFrequency.CUSTOM: 3,
        }
        self.frequency_combo.setCurrentIndex(
            freq_index_map.get(self.habit.frequency, 0)
        )

        if self.habit.custom_interval_days:
            self.custom_interval_spin.setValue(self.habit.custom_interval_days)

        if self.habit.target_value is not None:
            self.target_value_spin.setValue(self.habit.target_value)

        if self.habit.unit:
            self.unit_edit.setText(self.habit.unit)

        if self.habit.min_value is not None:
            self.min_value_spin.setValue(self.habit.min_value)

        if self.habit.max_value is not None:
            self.max_value_spin.setValue(self.habit.max_value)

        self.current_color = self.habit.color
        self.color_preview.setStyleSheet(
            f"background-color: {self.current_color}; border: 1px solid #ccc; border-radius: 3px;"
        )

        if self.habit.tags:
            self.tags_edit.setText(", ".join(self.habit.tags))

        self.active_check.setChecked(self.habit.active)

    def on_habit_type_changed(self, index: int):
        """Handle habit type change."""
        # Clear existing widgets
        while self.type_settings_layout.rowCount() > 0:
            self.type_settings_layout.removeRow(0)

        if index == 0:  # Boolean
            # No additional settings needed
            pass
        elif index == 1:  # Duration
            self.unit_edit.setText("minutes")
            self.unit_edit.setEnabled(False)
        elif index == 2:  # Units
            self.unit_edit.setEnabled(True)
            self.unit_edit.setPlaceholderText("e.g., steps, pages, glasses")
        elif index == 3:  # Real Number
            self.unit_edit.setEnabled(True)
            self.unit_edit.setPlaceholderText("e.g., kg, miles, hours")
        elif index == 4:  # Rating
            self.rating_scale_spin = QSpinBox()
            self.rating_scale_spin.setRange(2, 20)
            self.rating_scale_spin.setValue(10)
            self.type_settings_layout.addRow("Rating scale:", self.rating_scale_spin)
            self.unit_edit.setText("points")
            self.unit_edit.setEnabled(False)
        elif index == 5:  # Count
            self.unit_edit.setEnabled(True)
            self.unit_edit.setPlaceholderText("e.g., times, items")

    def on_frequency_changed(self, index: int):
        """Handle frequency change."""
        self.custom_interval_spin.setVisible(index == 3)  # Custom

    def choose_color(self):
        """Open color picker dialog."""
        color = QColorDialog.getColor(
            QColor(self.current_color), self, "Choose Habit Color"
        )
        if color.isValid():
            self.current_color = color.name()
            self.color_preview.setStyleSheet(
                f"background-color: {self.current_color}; border: 1px solid #ccc; border-radius: 3px;"
            )

    def get_habit(self) -> Optional[Habit]:
        """Get the habit data from the dialog."""
        name = self.name_edit.text().strip()
        if not name:
            return None

        # Get habit type
        type_map = [
            HabitType.BOOLEAN,
            HabitType.DURATION,
            HabitType.UNITS,
            HabitType.REAL_NUMBER,
            HabitType.RATING,
            HabitType.COUNT,
        ]
        habit_type = type_map[self.habit_type_combo.currentIndex()]

        # Get frequency
        freq_map = [
            HabitFrequency.DAILY,
            HabitFrequency.WEEKLY,
            HabitFrequency.MONTHLY,
            HabitFrequency.CUSTOM,
        ]
        frequency = freq_map[self.frequency_combo.currentIndex()]

        # Get custom interval
        custom_interval_days = None
        if frequency == HabitFrequency.CUSTOM:
            custom_interval_days = self.custom_interval_spin.value()

        # Get target value
        target_value = self.target_value_spin.value()
        # Only set to None if it's exactly 0 and the user hasn't explicitly set a target
        # For real number habits, 0.0 might be a valid target
        if (
            target_value == 0.0 and self.habit_type_combo.currentIndex() != 3
        ):  # Not REAL_NUMBER
            target_value = None

        # Get unit
        unit = self.unit_edit.text().strip()
        if not unit:
            unit = None

        # Get min/max values
        min_value = self.min_value_spin.value()
        if min_value == -999999:
            min_value = None

        max_value = self.max_value_spin.value()
        if max_value == 999999:
            max_value = None
        elif max_value == 0.0:
            # 0.0 is not a reasonable maximum for most habits, treat as no maximum
            max_value = None

        # Get rating scale
        rating_scale = 10
        if habit_type == HabitType.RATING and hasattr(self, "rating_scale_spin"):
            rating_scale = self.rating_scale_spin.value()

        # Get tags
        tags_text = self.tags_edit.text().strip()
        tags = (
            [tag.strip() for tag in tags_text.split(",") if tag.strip()]
            if tags_text
            else []
        )

        # Create habit data
        habit_data = {
            "name": name,
            "description": self.description_edit.toPlainText().strip() or None,
            "habit_type": habit_type,
            "frequency": frequency,
            "custom_interval_days": custom_interval_days,
            "target_value": target_value,
            "unit": unit,
            "color": self.current_color,
            "active": self.active_check.isChecked(),
            "min_value": min_value,
            "max_value": max_value,
            "rating_scale": rating_scale,
            "tags": tags,
        }

        if self.is_editing:
            # Update existing habit
            habit_data["id"] = self.habit.id
            habit_data["created_at"] = self.habit.created_at
            habit_data["updated_at"] = datetime.now()
            habit_data["recent_entries"] = self.habit.recent_entries
        else:
            # Create new habit
            habit_data["id"] = 0  # Will be set by database
            habit_data["created_at"] = datetime.now()
            habit_data["updated_at"] = datetime.now()
            habit_data["recent_entries"] = []

        return Habit(**habit_data)
