"""
Task info dialog for the Cando application.

This module provides a simple dialog for displaying task information
in a read-only format similar to the editing dialog.
"""

from typing import List
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QFrame,
    QScrollArea,
    QWidget,
    QListWidget,
    QListWidgetItem,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from app.models.task import Task
from app.ui.base_dialog import BaseDialog


class TaskInfoDialog(BaseDialog):
    """
    Dialog for displaying task information in a read-only format.

    Shows task name, tags, and status in a simple, organized layout
    similar to the editing dialog but with only a close button.
    """

    def __init__(self, task: Task, parent=None):
        """
        Initialize the task info dialog.

        Args:
            task: Task to display information for
            parent: Parent widget
        """
        super().__init__(parent)
        self.task = task

        self.setWindowTitle(f"Task Info: {self.task.name}")
        self.setModal(True)

        self.setup_ui()
        self.load_task_data()
        self.setup_compact_sizing()

    def setup_compact_sizing(self):
        """Set up compact sizing for the info dialog."""
        # Override the large sizing from BaseDialog with a more appropriate size
        self.setFixedSize(400, 350)  # Use setFixedSize like the tag dialog

    def showEvent(self, event):
        """Override showEvent to center the dialog after it's shown."""
        super().showEvent(event)
        # Center the dialog after it's shown
        self.center_dialog()

    def center_dialog(self):
        """Center the dialog on screen."""
        # Get the screen geometry
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app and app.primaryScreen():
            screen_rect = app.primaryScreen().geometry()
            x = (screen_rect.width() - self.width()) // 2
            y = (screen_rect.height() - self.height()) // 2
            self.move(x, y)

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Create scroll area for better UX
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Basic information section
        basic_group = self.create_basic_info_section()
        scroll_layout.addWidget(basic_group)

        # Status section
        status_group = self.create_status_section()
        scroll_layout.addWidget(status_group)

        # Tags section
        tags_group = self.create_tags_section()
        scroll_layout.addWidget(tags_group)

        # Close button
        button_layout = QHBoxLayout()
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)

        button_layout.addStretch()
        button_layout.addWidget(self.close_button)

        scroll_layout.addLayout(button_layout)

        # Set up scroll area
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

    def create_basic_info_section(self) -> QFrame:
        """Create the basic information section."""
        group = QFrame()
        group.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(group)

        # Title
        title = QLabel("Basic Information")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)

        # Form layout
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setReadOnly(True)
        form_layout.addRow("Name:", self.name_edit)

        layout.addLayout(form_layout)
        return group

    def create_status_section(self) -> QFrame:
        """Create the status section."""
        group = QFrame()
        group.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(group)

        # Title
        title = QLabel("Status")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)

        # Form layout
        form_layout = QFormLayout()

        self.status_edit = QLineEdit()
        self.status_edit.setReadOnly(True)
        form_layout.addRow("Status:", self.status_edit)

        self.priority_edit = QLineEdit()
        self.priority_edit.setReadOnly(True)
        form_layout.addRow("Priority:", self.priority_edit)

        layout.addLayout(form_layout)
        return group

    def create_tags_section(self) -> QFrame:
        """Create the tags display section."""
        group = QFrame()
        group.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(group)

        # Title
        title = QLabel("Tags")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)

        # Tags list
        self.tags_list = QListWidget()
        self.tags_list.setMaximumHeight(120)
        self.tags_list.setSelectionMode(QListWidget.NoSelection)
        layout.addWidget(self.tags_list)

        return group

    def load_task_data(self):
        """Load task data into the form."""
        # Basic info
        self.name_edit.setText(self.task.name)

        # Status
        status_text = "Completed" if self.task.completed else "Active"
        self.status_edit.setText(status_text)
        self.priority_edit.setText(self.task.priority)

        # Tags
        if self.task.tags:
            for tag in self.task.tags:
                # Handle both old string format and new dict format
                if isinstance(tag, dict):
                    self.add_tag_to_list(tag["name"])
                else:
                    self.add_tag_to_list(tag)
        else:
            # Add a placeholder item when no tags
            item = QListWidgetItem("No tags assigned")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.tags_list.addItem(item)

    def add_tag_to_list(self, tag_name: str):
        """Add a tag to the tags list."""
        item = QListWidgetItem(tag_name)
        item.setFlags(item.flags() & ~Qt.ItemIsSelectable)  # Make read-only
        self.tags_list.addItem(item)

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
