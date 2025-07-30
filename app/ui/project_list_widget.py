"""
Project list widget for the Cando application.

This module provides a custom list widget for displaying projects
with rich information including priority, status, due dates, and tags.
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
from PySide6.QtGui import QFont, QColor, QPalette, QMouseEvent
from app.models.project import Project
from app.utils.fuzzy_search import highlight_search_terms


class ProjectItemWidget(QWidget):
    """
    Custom widget for displaying project information in a list item.

    Shows project name, description, priority, status, due date, and tags
    with color coding and visual indicators.
    """

    def __init__(self, project: Project, search_query: str = "", parent=None):
        """Initialize the project item widget."""
        super().__init__(parent)
        self.project = project
        self.search_query = search_query
        self.setup_ui()

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            # Check if Ctrl is pressed for info dialog
            if event.modifiers() & Qt.ControlModifier:
                from app.ui.project_info_dialog import ProjectInfoDialog

                dialog = ProjectInfoDialog(self.project, self)
                dialog.exec()  # Use exec() instead of show() for modal behavior
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double click events to open edit dialog."""
        if event.button() == Qt.LeftButton:
            # Find the parent ProjectListWidget and emit edit signal
            parent = self.parent()
            while parent and not hasattr(parent, "project_edit_requested"):
                parent = parent.parent()

            if parent and hasattr(parent, "project_edit_requested"):
                parent.project_edit_requested.emit(self.project)
            return

        super().mouseDoubleClickEvent(event)

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Set tooltip for info dialog access
        self.setToolTip("Ctrl+Click to view project details")

        # Main project info
        main_layout = QHBoxLayout()

        # Project name and description
        info_layout = QVBoxLayout()

        # Highlight search terms in project name
        name_text = self.project.name
        if self.search_query:
            name_text = highlight_search_terms(name_text, self.search_query)

        name_label = QLabel(name_text)
        name_label.setFont(QFont("Arial", 10, QFont.Bold))
        name_label.setStyleSheet(f"color: {self.get_text_color()};")
        name_label.setTextFormat(Qt.RichText)
        info_layout.addWidget(name_label)

        if self.project.description:
            # Highlight search terms in description
            desc_text = (
                self.project.description[:100] + "..."
                if len(self.project.description) > 100
                else self.project.description
            )
            if self.search_query:
                desc_text = highlight_search_terms(desc_text, self.search_query)

            desc_label = QLabel(desc_text)
            desc_label.setFont(QFont("Arial", 8))
            # Use theme-aware secondary text color
            palette = self.palette()
            desc_label.setStyleSheet(f"color: {palette.color(QPalette.Mid).name()};")
            desc_label.setTextFormat(Qt.RichText)
            info_layout.addWidget(desc_label)

        main_layout.addLayout(info_layout)
        main_layout.addStretch()

        # Priority and status indicators
        indicators_layout = QVBoxLayout()

        # Priority indicator
        priority_frame = QFrame()
        priority_frame.setFixedSize(12, 12)
        priority_frame.setStyleSheet(
            f"background-color: {self.project.priority_color}; border-radius: 6px;"
        )
        priority_layout = QHBoxLayout()
        priority_layout.addWidget(priority_frame)
        priority_layout.addWidget(QLabel(self.project.priority.upper()))
        priority_layout.addStretch()
        indicators_layout.addLayout(priority_layout)

        # Status indicator
        status_frame = QFrame()
        status_frame.setFixedSize(12, 12)
        status_frame.setStyleSheet(
            f"background-color: {self.project.status_color}; border-radius: 6px;"
        )
        status_layout = QHBoxLayout()
        status_layout.addWidget(status_frame)
        status_layout.addWidget(QLabel(self.project.status.upper()))
        status_layout.addStretch()
        indicators_layout.addLayout(status_layout)

        main_layout.addLayout(indicators_layout)

        layout.addLayout(main_layout)

        # Secondary info (due date, estimated hours, tags)
        secondary_layout = QHBoxLayout()

        # Due date
        if self.project.due_date:
            due_text = f"Due: {self.project.due_date.strftime('%Y-%m-%d')}"
            if self.project.is_overdue:
                due_text += " (OVERDUE)"
                due_color = "#dc3545"  # Red for overdue
            elif (
                self.project.days_remaining is not None
                and self.project.days_remaining <= 3
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
        if self.project.estimated_hours:
            hours_label = QLabel(f"Est: {self.project.estimated_hours}h")
            hours_label.setFont(QFont("Arial", 8))
            hours_label.setStyleSheet("color: #6c757d;")
            secondary_layout.addWidget(hours_label)

        # Tags
        if self.project.tags:
            tags_layout = QHBoxLayout()
            tags_layout.setSpacing(4)

            # Create a container widget for tags to enable hover tooltip
            tags_container = QWidget()
            tags_container_layout = QHBoxLayout(tags_container)
            tags_container_layout.setSpacing(4)
            tags_container_layout.setContentsMargins(0, 0, 0, 0)

            # Display first 3 tags with colors
            for i, tag in enumerate(self.project.tags[:3]):
                tag_label = QLabel(tag["name"])
                tag_label.setFont(QFont("Arial", 8))
                tag_label.setStyleSheet(
                    f"color: white; background-color: {tag['color']}; "
                    f"padding: 2px 6px; border-radius: 8px;"
                )
                tags_container_layout.addWidget(tag_label)

            if len(self.project.tags) > 3:
                more_label = QLabel("...")
                more_label.setFont(QFont("Arial", 8))
                more_label.setStyleSheet("color: #6c757d;")
                tags_container_layout.addWidget(more_label)

            # Add stretch to make tags take all available space
            tags_container_layout.addStretch()

            secondary_layout.addWidget(tags_container)

        layout.addLayout(secondary_layout)

    def get_text_color(self) -> str:
        """Get appropriate text color based on project status."""
        if self.project.status == "completed":
            return "#28a745"  # Green
        elif self.project.status == "cancelled":
            return "#6c757d"  # Gray
        else:
            # Use theme-aware color instead of hardcoded white
            palette = self.palette()
            return palette.color(QPalette.Text).name()


class ProjectListWidget(QListWidget):
    """
    Custom list widget for displaying projects with rich information.

    Provides context menu for editing and deleting projects,
    and visual indicators for project status and priority.
    """

    project_edit_requested = Signal(Project)
    project_delete_requested = Signal(Project)
    project_selected = Signal(Project)

    def __init__(self, parent=None):
        """Initialize the project list widget."""
        super().__init__(parent)
        self._programmatic_selection = (
            False  # Flag to prevent signal emission during programmatic selection
        )
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        self.setAlternatingRowColors(True)
        self.setSpacing(2)
        self.itemClicked.connect(self.on_item_clicked)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def add_project(self, project: Project, search_query: str = ""):
        """Add a project to the list."""
        item = QListWidgetItem(self)
        item_widget = ProjectItemWidget(project, search_query)
        item.setSizeHint(item_widget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, item_widget)
        item.setData(Qt.UserRole, project)

    def update_projects(self, projects: List[Project], search_query: str = ""):
        """Update the list with new projects."""
        self.clear()
        for project in projects:
            self.add_project(project, search_query)

    def get_selected_project(self) -> Optional[Project]:
        """Get the currently selected project."""
        current_item = self.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole)
        return None

    def set_selected_project(self, project: Project):
        """Set the selected project programmatically."""
        self._programmatic_selection = True
        for i in range(self.count()):
            item = self.item(i)
            item_project = item.data(Qt.UserRole)
            if (
                item_project and item_project.id == project.id
            ):  # Compare by ID instead of object reference
                self.setCurrentItem(item)
                break
        self._programmatic_selection = False

    def on_item_clicked(self, item: QListWidgetItem):
        """Handle item click."""
        project = item.data(Qt.UserRole)
        if project and not self._programmatic_selection:
            self.project_selected.emit(project)

    def show_context_menu(self, position):
        """Show context menu for the clicked item."""
        item = self.itemAt(position)
        if not item:
            return

        project = item.data(Qt.UserRole)
        if not project:
            return

        menu = QMenu(self)

        edit_action = menu.addAction("Edit Project")
        edit_action.triggered.connect(lambda: self.project_edit_requested.emit(project))

        delete_action = menu.addAction("Delete Project")
        delete_action.triggered.connect(lambda: self.confirm_delete_project(project))

        menu.exec_(self.mapToGlobal(position))

    def confirm_delete_project(self, project: Project):
        """Confirm project deletion."""
        reply = QMessageBox.question(
            self,
            "Delete Project",
            f"Are you sure you want to delete project '{project.name}'?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.project_delete_requested.emit(project)
