"""
Habit list widget for the Cando application.

This module provides a widget for displaying and managing habits
with various tracking types and entry management.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QScrollArea,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QLineEdit,
    QTextEdit,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QColorDialog,
    QMessageBox,
    QGroupBox,
    QGridLayout,
)
from PySide6.QtCore import Qt, Signal, QTimer, QDate
from PySide6.QtGui import QFont, QColor, QPalette
from datetime import datetime, date, timedelta
from typing import List, Optional, Union
from app.models.habit import Habit, HabitEntry, HabitType, HabitFrequency
from app.ui.habit_dialog import HabitDialog
from app.ui.habit_entry_dialog import HabitEntryDialog


class HabitItemWidget(QWidget):
    """Widget for displaying a single habit item."""

    entry_added = Signal(Habit, HabitEntry)  # Emitted when a new entry is added
    habit_updated = Signal(Habit)  # Emitted when habit is updated
    habit_deleted = Signal(int)  # Emitted when habit is deleted

    def __init__(self, habit: Habit, parent=None):
        super().__init__(parent)
        self.habit = habit
        self.setup_ui()
        self.update_display()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # Main habit info
        info_layout = QHBoxLayout()

        # Color indicator
        self.color_indicator = QFrame()
        self.color_indicator.setFixedSize(16, 16)
        self.color_indicator.setStyleSheet(
            f"background-color: {self.habit.color}; border-radius: 8px;"
        )
        info_layout.addWidget(self.color_indicator)

        # Habit name and description
        name_layout = QVBoxLayout()
        self.name_label = QLabel(self.habit.name)
        self.name_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        name_layout.addWidget(self.name_label)

        if self.habit.description:
            self.desc_label = QLabel(self.habit.description)
            self.desc_label.setWordWrap(True)
            self.desc_label.setStyleSheet("color: #888888; font-size: 10px;")
            name_layout.addWidget(self.desc_label)

        info_layout.addLayout(name_layout)
        info_layout.addStretch()

        # Status indicators
        status_layout = QVBoxLayout()

        # Today's status
        self.today_status = QLabel()
        self.today_status.setAlignment(Qt.AlignRight)
        status_layout.addWidget(self.today_status)

        # Streak info
        self.streak_label = QLabel()
        self.streak_label.setAlignment(Qt.AlignRight)
        self.streak_label.setStyleSheet("color: #007bff; font-size: 10px;")
        status_layout.addWidget(self.streak_label)

        info_layout.addLayout(status_layout)
        layout.addLayout(info_layout)

        # Tags
        if self.habit.tags:
            tags_layout = QHBoxLayout()
            tags_layout.addWidget(QLabel("Tags:"))
            for tag in self.habit.tags:
                tag_label = QLabel(tag)
                tag_label.setStyleSheet(
                    "background-color: #2d2d30; padding: 2px 6px; border-radius: 3px; font-size: 9px;"
                )
                tags_layout.addWidget(tag_label)
            tags_layout.addStretch()
            layout.addLayout(tags_layout)

        # Action buttons
        button_layout = QHBoxLayout()

        # Add entry button
        self.add_entry_btn = QPushButton("Add Entry")
        self.add_entry_btn.clicked.connect(self.add_entry)
        button_layout.addWidget(self.add_entry_btn)

        # Quick entry buttons based on habit type
        if self.habit.habit_type == HabitType.BOOLEAN:
            self.quick_yes_btn = QPushButton("✓ Yes")
            self.quick_yes_btn.clicked.connect(lambda: self.quick_add_entry(True))
            self.quick_no_btn = QPushButton("✗ No")
            self.quick_no_btn.clicked.connect(lambda: self.quick_add_entry(False))
            button_layout.addWidget(self.quick_yes_btn)
            button_layout.addWidget(self.quick_no_btn)
        elif self.habit.habit_type == HabitType.RATING:
            self.rating_combo = QComboBox()
            self.rating_combo.addItems(
                [str(i) for i in range(1, self.habit.rating_scale + 1)]
            )
            self.rating_combo.currentTextChanged.connect(self.quick_rating_entry)
            button_layout.addWidget(QLabel("Rating:"))
            button_layout.addWidget(self.rating_combo)

        button_layout.addStretch()

        # Edit and delete buttons
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.edit_habit)
        button_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_habit)
        self.delete_btn.setProperty("class", "danger-button")
        button_layout.addWidget(self.delete_btn)

        layout.addLayout(button_layout)

        # Set minimum height for better appearance
        self.setMinimumHeight(120)

    def update_display(self):
        """Update the display with current habit data."""
        # Update today's status
        today_value = self.habit.get_today_value()
        if today_value is not None:
            if self.habit.habit_type == HabitType.BOOLEAN:
                status_text = "✓ Completed" if today_value else "✗ Not done"
                status_color = "#28a745" if today_value else "#dc3545"
            else:
                display_value = self.habit.get_display_value(today_value)
                status_text = f"Today: {display_value}"
                if self.habit.target_value and today_value >= self.habit.target_value:
                    status_color = "#28a745"
                else:
                    status_color = "#ffc107"
        else:
            status_text = "No entry today"
            status_color = "#6c757d"

        self.today_status.setText(status_text)
        self.today_status.setStyleSheet(f"color: {status_color}; font-weight: bold;")

        # Update streak
        streak = self.habit.get_streak_days()
        if streak > 0:
            self.streak_label.setText(f"🔥 {streak} day streak")
        else:
            self.streak_label.setText("No streak")

    def add_entry(self):
        """Open dialog to add a new habit entry."""
        dialog = HabitEntryDialog(self.habit, self)
        if dialog.exec() == QDialog.Accepted:
            entry = dialog.get_entry()
            if entry:
                self.entry_added.emit(self.habit, entry)
                self.update_display()

    def quick_add_entry(self, value: Union[bool, int, float]):
        """Quickly add an entry with the given value."""
        today = date.today()

        # Check if entry already exists for today
        existing_value = self.habit.get_today_value()
        if existing_value is not None:
            reply = QMessageBox.question(
                self,
                "Entry Exists",
                f"An entry already exists for today ({self.habit.get_display_value(existing_value)}). Replace it?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return

        entry = HabitEntry(
            id=0,  # Will be set by database
            habit_id=self.habit.id,
            date=today,
            value=value,
            notes="",
        )
        self.entry_added.emit(self.habit, entry)
        self.update_display()

    def quick_rating_entry(self, rating_text: str):
        """Quickly add a rating entry."""
        try:
            rating = int(rating_text)
            self.quick_add_entry(rating)
        except ValueError:
            pass

    def edit_habit(self):
        """Open dialog to edit the habit."""
        dialog = HabitDialog(self.habit, self)
        if dialog.exec() == QDialog.Accepted:
            updated_habit = dialog.get_habit()
            if updated_habit:
                self.habit = updated_habit
                self.habit_updated.emit(updated_habit)
                self.update_display()

    def delete_habit(self):
        """Delete the habit after confirmation."""
        reply = QMessageBox.question(
            self,
            "Delete Habit",
            f"Are you sure you want to delete '{self.habit.name}'? This will also delete all its entries.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.habit_deleted.emit(self.habit.id)


class HabitListWidget(QWidget):
    """Widget for displaying and managing a list of habits."""

    habit_created = Signal(Habit)
    habit_updated = Signal(Habit)
    habit_deleted = Signal(int)
    entry_added = Signal(Habit, HabitEntry)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.habits = []
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Habits")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Add habit button
        self.add_habit_btn = QPushButton("+ Add Habit")
        self.add_habit_btn.clicked.connect(self.add_habit)
        header_layout.addWidget(self.add_habit_btn)

        layout.addLayout(header_layout)

        # Habits list
        self.habits_list = QListWidget()
        self.habits_list.setSpacing(5)
        self.habits_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        layout.addWidget(self.habits_list)

    def set_habits(self, habits: List[Habit]):
        """Set the list of habits to display."""
        self.habits = habits
        self.refresh_display()

    def refresh_display(self):
        """Refresh the display of habits."""
        self.habits_list.clear()

        for habit in self.habits:
            item = QListWidgetItem()
            habit_widget = HabitItemWidget(habit)

            # Connect signals
            habit_widget.entry_added.connect(self.entry_added.emit)
            habit_widget.habit_updated.connect(self.habit_updated.emit)
            habit_widget.habit_deleted.connect(self.habit_deleted.emit)

            self.habits_list.addItem(item)
            self.habits_list.setItemWidget(item, habit_widget)
            item.setSizeHint(habit_widget.sizeHint())

    def add_habit(self):
        """Open dialog to create a new habit."""
        dialog = HabitDialog(None, self)
        if dialog.exec() == QDialog.Accepted:
            habit = dialog.get_habit()
            if habit:
                self.habit_created.emit(habit)

    def add_habit_to_list(self, habit: Habit):
        """Add a new habit to the display."""
        self.habits.append(habit)
        self.refresh_display()

    def update_habit_in_list(self, habit: Habit):
        """Update a habit in the display."""
        for i, existing_habit in enumerate(self.habits):
            if existing_habit.id == habit.id:
                self.habits[i] = habit
                break
        self.refresh_display()

    def remove_habit_from_list(self, habit_id: int):
        """Remove a habit from the display."""
        self.habits = [h for h in self.habits if h.id != habit_id]
        self.refresh_display()
