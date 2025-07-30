"""
Project dialog for the Cando application.

This module provides a dialog for creating and editing projects
with all project fields and tag management.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QDateEdit,
    QSpinBox,
    QComboBox,
    QPushButton,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QFrame,
    QScrollArea,
    QWidget,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor
from app.models.project import Project
from app.ui.base_dialog import BaseDialog


class ProjectDialog(BaseDialog):
    """
    Dialog for creating and editing projects.

    Provides a comprehensive interface for managing all project fields
    including tags, priority, status, and time estimates.
    """

    def __init__(self, parent=None, project: Optional[Project] = None):
        """
        Initialize the project dialog.

        Args:
            parent: Parent widget
            project: Existing project to edit (None for new project)
        """
        super().__init__(parent)
        self.project = project
        self.is_editing = project is not None

        self.setWindowTitle("Edit Project" if self.is_editing else "New Project")
        self.setModal(True)

        self.setup_ui()
        self.load_project_data()

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

        # Dates and time section
        time_group = self.create_time_section()
        scroll_layout.addWidget(time_group)

        # Priority and status section
        status_group = self.create_status_section()
        scroll_layout.addWidget(status_group)

        # Tags section
        tags_group = self.create_tags_section()
        scroll_layout.addWidget(tags_group)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        self.delete_button = QPushButton("Delete")

        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.delete_button.clicked.connect(self.delete_project)

        # Only show delete button when editing
        self.delete_button.setVisible(self.is_editing)

        button_layout.addStretch()
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)

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
        self.name_edit.setPlaceholderText("Enter project name")
        form_layout.addRow("Name:", self.name_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setPlaceholderText("Enter project description")
        form_layout.addRow("Description:", self.description_edit)

        layout.addLayout(form_layout)
        return group

    def create_time_section(self) -> QFrame:
        """Create the time and dates section."""
        group = QFrame()
        group.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(group)

        # Title
        title = QLabel("Time & Dates")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)

        # Form layout
        form_layout = QFormLayout()

        self.due_date_edit = QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDate(
            QDate.currentDate().addDays(7)
        )  # Default to 1 week from now
        form_layout.addRow("Due Date:", self.due_date_edit)

        self.estimated_hours_edit = QSpinBox()
        self.estimated_hours_edit.setRange(0, 1000)
        self.estimated_hours_edit.setSuffix(" hours")
        self.estimated_hours_edit.setValue(8)  # Default to 8 hours
        form_layout.addRow("Estimated Hours:", self.estimated_hours_edit)

        layout.addLayout(form_layout)
        return group

    def create_status_section(self) -> QFrame:
        """Create the priority and status section."""
        group = QFrame()
        group.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(group)

        # Title
        title = QLabel("Priority & Status")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)

        # Form layout
        form_layout = QFormLayout()

        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["low", "medium", "high", "urgent"])
        self.priority_combo.setCurrentText("medium")
        form_layout.addRow("Priority:", self.priority_combo)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["active", "paused", "completed", "cancelled"])
        self.status_combo.setCurrentText("active")
        form_layout.addRow("Status:", self.status_combo)

        layout.addLayout(form_layout)
        return group

    def create_tags_section(self) -> QFrame:
        """Create the tags management section."""
        group = QFrame()
        group.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(group)

        # Title
        title = QLabel("Tags")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)

        # Tag input
        tag_layout = QHBoxLayout()
        self.tag_edit = QLineEdit()
        self.tag_edit.setPlaceholderText("Enter tag name")
        self.add_tag_button = QPushButton("Add Tag")
        self.add_tag_button.clicked.connect(self.add_tag)

        tag_layout.addWidget(self.tag_edit)
        tag_layout.addWidget(self.add_tag_button)
        layout.addLayout(tag_layout)

        # Tags list
        self.tags_list = QListWidget()
        self.tags_list.setMaximumHeight(120)
        layout.addWidget(self.tags_list)

        # Remove tag button
        self.remove_tag_button = QPushButton("Remove Selected Tag")
        self.remove_tag_button.clicked.connect(self.remove_tag)
        layout.addWidget(self.remove_tag_button)

        return group

    def load_project_data(self):
        """Load existing project data into the form."""
        if not self.project:
            return

        # Basic info
        self.name_edit.setText(self.project.name)
        self.description_edit.setPlainText(self.project.description)

        # Dates and time
        if self.project.due_date:
            self.due_date_edit.setDate(QDate(self.project.due_date))
        if self.project.estimated_hours:
            self.estimated_hours_edit.setValue(int(self.project.estimated_hours))

        # Priority and status
        self.priority_combo.setCurrentText(self.project.priority)
        self.status_combo.setCurrentText(self.project.status)

        # Tags
        for tag in self.project.tags:
            self.add_tag_to_list(tag)

    def add_tag(self):
        """Add a new tag to the project."""
        tag_name = self.tag_edit.text().strip()
        if not tag_name:
            return

        # Check if tag already exists
        for i in range(self.tags_list.count()):
            if self.tags_list.item(i).text() == tag_name:
                QMessageBox.warning(
                    self, "Duplicate Tag", f"Tag '{tag_name}' already exists."
                )
                return

        self.add_tag_to_list(tag_name)
        self.tag_edit.clear()

    def add_tag_to_list(self, tag_name: str):
        """Add a tag to the tags list."""
        item = QListWidgetItem(tag_name)
        self.tags_list.addItem(item)

    def remove_tag(self):
        """Remove the selected tag."""
        current_item = self.tags_list.currentItem()
        if current_item:
            self.tags_list.takeItem(self.tags_list.row(current_item))

    def get_tags(self) -> List[str]:
        """Get all tags from the list."""
        tags = []
        for i in range(self.tags_list.count()):
            tags.append(self.tags_list.item(i).text())
        return tags

    def delete_project(self):
        """Delete the current project."""
        reply = QMessageBox.question(
            self,
            "Delete Project",
            f"Are you sure you want to delete project '{self.project.name}'?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.project = None
            self.accept()

    def get_project_data(self) -> dict:
        """Get all form data as a dictionary."""
        due_date = (
            self.due_date_edit.date().toPython()
            if self.due_date_edit.date().isValid()
            else None
        )
        estimated_hours = (
            self.estimated_hours_edit.value()
            if self.estimated_hours_edit.value() > 0
            else None
        )

        return {
            "name": self.name_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip(),
            "due_date": due_date,
            "estimated_hours": estimated_hours,
            "priority": self.priority_combo.currentText(),
            "status": self.status_combo.currentText(),
            "tags": self.get_tags(),
        }

    def validate_data(self) -> bool:
        """Validate the form data."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Project name is required.")
            self.name_edit.setFocus()
            return False

        return True

    def accept(self):
        """Handle dialog acceptance with validation."""
        if not self.validate_data():
            return

        super().accept()
