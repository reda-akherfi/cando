"""
Task list widget for the Cando application.

This module provides a custom list widget for displaying tasks
with rich information including priority, completion status, due dates, and tags.
"""

from datetime import datetime
from typing import List, Optional
from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QMenu,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QPalette
from app.models.task import Task
from app.utils.fuzzy_search import highlight_search_terms


class TaskItemWidget(QWidget):
    """
    Custom widget for displaying task information in a list item.

    Shows task name, description, priority, completion status, due date, and tags
    with color coding and visual indicators.
    """

    def __init__(self, task: Task, search_query: str = "", parent=None):
        """Initialize the task item widget."""
        super().__init__(parent)
        self.task = task
        self.search_query = search_query
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Main task info
        main_layout = QHBoxLayout()

        # Task name and description
        info_layout = QVBoxLayout()

        # Highlight search terms in task name
        name_text = self.task.name
        if self.search_query:
            name_text = highlight_search_terms(name_text, self.search_query)

        name_label = QLabel(name_text)
        name_label.setFont(QFont("Arial", 10, QFont.Bold))
        name_label.setStyleSheet(f"color: {self.get_text_color()};")
        name_label.setTextFormat(Qt.RichText)
        info_layout.addWidget(name_label)

        if self.task.description:
            # Highlight search terms in description
            desc_text = (
                self.task.description[:100] + "..."
                if len(self.task.description) > 100
                else self.task.description
            )
            if self.search_query:
                desc_text = highlight_search_terms(desc_text, self.search_query)

            desc_label = QLabel(desc_text)
            desc_label.setFont(QFont("Arial", 8))
            desc_label.setStyleSheet("color: #888888;")
            desc_label.setTextFormat(Qt.RichText)
            info_layout.addWidget(desc_label)

        main_layout.addLayout(info_layout)
        main_layout.addStretch()

        # Priority and completion indicators
        indicators_layout = QVBoxLayout()

        # Priority indicator
        priority_frame = QFrame()
        priority_frame.setFixedSize(12, 12)
        priority_frame.setStyleSheet(
            f"background-color: {self.task.priority_color}; border-radius: 6px;"
        )
        priority_layout = QHBoxLayout()
        priority_layout.addWidget(priority_frame)
        priority_layout.addWidget(QLabel(self.task.priority.upper()))
        priority_layout.addStretch()
        indicators_layout.addLayout(priority_layout)

        # Completion indicator
        completion_text = "✓ COMPLETED" if self.task.completed else "○ PENDING"
        completion_color = "#28a745" if self.task.completed else "#ffc107"
        completion_label = QLabel(completion_text)
        completion_label.setFont(QFont("Arial", 8, QFont.Bold))
        completion_label.setStyleSheet(f"color: {completion_color};")
        indicators_layout.addWidget(completion_label)

        main_layout.addLayout(indicators_layout)

        layout.addLayout(main_layout)

        # Secondary info (due date, estimated hours, tags)
        secondary_layout = QHBoxLayout()

        # Due date
        if self.task.due_date:
            due_text = f"Due: {self.task.due_date.strftime('%Y-%m-%d')}"
            if self.task.is_overdue and not self.task.completed:
                due_text += " (OVERDUE)"
                due_color = "#dc3545"  # Red for overdue
            elif (
                self.task.days_remaining is not None
                and self.task.days_remaining <= 1
                and not self.task.completed
            ):
                due_color = "#fd7e14"  # Orange for urgent
            else:
                due_color = "#6c757d"  # Gray for normal

            due_label = QLabel(due_text)
            due_label.setFont(QFont("Arial", 8))
            due_label.setStyleSheet(f"color: {due_color};")
            secondary_layout.addWidget(due_label)

        secondary_layout.addStretch()

        # Estimated hours
        if hasattr(self.task, "estimated_hours") and self.task.estimated_hours:
            hours_label = QLabel(f"Est: {self.task.estimated_hours}h")
            hours_label.setFont(QFont("Arial", 8))
            hours_label.setStyleSheet("color: #6c757d;")
            secondary_layout.addWidget(hours_label)

        # Tags
        if self.task.tags:
            tags_label = QLabel(f"Tags: {', '.join(self.task.tags[:2])}")
            if len(self.task.tags) > 2:
                tags_label.setText(tags_label.text() + "...")
            tags_label.setFont(QFont("Arial", 8))
            tags_label.setStyleSheet("color: #007bff;")
            secondary_layout.addWidget(tags_label)

        layout.addLayout(secondary_layout)

    def get_text_color(self) -> str:
        """Get appropriate text color based on task status."""
        if self.task.completed:
            return "#28a745"  # Green for completed
        elif self.task.is_overdue:
            return "#dc3545"  # Red for overdue
        else:
            return "#ffffff"  # White for active


class TaskListWidget(QListWidget):
    """
    Custom list widget for displaying tasks with rich information.

    Provides context menu for editing and deleting tasks,
    and visual indicators for task status and priority.
    """

    task_edit_requested = Signal(Task)
    task_delete_requested = Signal(Task)
    task_selected = Signal(Task)

    def __init__(self, parent=None):
        """Initialize the task list widget."""
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        self.setAlternatingRowColors(True)
        self.setSpacing(2)
        self.itemClicked.connect(self.on_item_clicked)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def add_task(self, task: Task, search_query: str = ""):
        """Add a task to the list."""
        item = QListWidgetItem(self)
        item_widget = TaskItemWidget(task, search_query)
        item.setSizeHint(item_widget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, item_widget)
        item.setData(Qt.UserRole, task)

    def update_tasks(self, tasks: List[Task], search_query: str = ""):
        """Update the list with new tasks."""
        self.clear()
        for task in tasks:
            self.add_task(task, search_query)

    def get_selected_task(self) -> Optional[Task]:
        """Get the currently selected task."""
        current_item = self.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole)
        return None

    def on_item_clicked(self, item: QListWidgetItem):
        """Handle item click."""
        task = item.data(Qt.UserRole)
        if task:
            self.task_selected.emit(task)

    def show_context_menu(self, position):
        """Show context menu for the clicked item."""
        item = self.itemAt(position)
        if not item:
            return

        task = item.data(Qt.UserRole)
        if not task:
            return

        menu = QMenu(self)

        edit_action = menu.addAction("Edit Task")
        edit_action.triggered.connect(lambda: self.task_edit_requested.emit(task))

        # Add toggle completion action
        if task.completed:
            toggle_action = menu.addAction("Mark as Pending")
        else:
            toggle_action = menu.addAction("Mark as Completed")
        toggle_action.triggered.connect(lambda: self.toggle_task_completion(task))

        delete_action = menu.addAction("Delete Task")
        delete_action.triggered.connect(lambda: self.confirm_delete_task(task))

        menu.exec_(self.mapToGlobal(position))

    def toggle_task_completion(self, task: Task):
        """Toggle task completion status."""
        # This will be handled by the main window
        self.task_edit_requested.emit(task)

    def confirm_delete_task(self, task: Task):
        """Confirm task deletion."""
        reply = QMessageBox.question(
            self,
            "Delete Task",
            f"Are you sure you want to delete task '{task.name}'?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.task_delete_requested.emit(task)
