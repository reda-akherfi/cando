"""
Tag list widget for the Cando application.

This module provides a custom list widget for displaying tags
with usage statistics, sorting, and management capabilities.
"""

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
    QComboBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QPalette, QMouseEvent
from app.models.tag import Tag
from app.utils.fuzzy_search import highlight_search_terms


class TagItemWidget(QWidget):
    """
    Custom widget for displaying tag information in a list item.

    Shows tag name, usage count, and linked items with color coding.
    """

    def __init__(self, tag: Tag, search_query: str = "", parent=None):
        """Initialize the tag item widget."""
        super().__init__(parent)
        self.tag = tag
        self.search_query = search_query
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Set tooltip for double-click functionality
        self.setToolTip("Double-click to edit tag")

        # Tag color indicator
        color_frame = QFrame()
        color_frame.setFixedSize(16, 16)
        color_frame.setStyleSheet(
            f"background-color: {self.tag.color}; border-radius: 8px; border: 1px solid #ccc;"
        )
        layout.addWidget(color_frame)

        # Tag info layout
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        # Tag name with search highlighting
        name_text = self.tag.name
        if self.search_query:
            name_text = highlight_search_terms(name_text, self.search_query)

        name_label = QLabel(name_text)
        name_label.setFont(QFont("Arial", 10, QFont.Bold))
        # Use theme-aware color instead of hardcoded white
        palette = self.palette()
        name_label.setStyleSheet(f"color: {palette.color(QPalette.Text).name()};")
        name_label.setTextFormat(Qt.RichText)
        info_layout.addWidget(name_label)

        # Tag description
        if self.tag.description:
            desc_label = QLabel(self.tag.description)
            desc_label.setFont(QFont("Arial", 8))
            # Use theme-aware secondary text color
            palette = self.palette()
            desc_label.setStyleSheet(f"color: {palette.color(QPalette.Mid).name()};")
            info_layout.addWidget(desc_label)

        layout.addLayout(info_layout)

        layout.addStretch()

        # Usage count
        usage_label = QLabel(f"Used {self.tag.usage_count} times")
        usage_label.setFont(QFont("Arial", 8))
        # Use theme-aware secondary text color
        palette = self.palette()
        usage_label.setStyleSheet(f"color: {palette.color(QPalette.Mid).name()};")
        layout.addWidget(usage_label)

        # Linked items info
        if self.tag.linked_projects or self.tag.linked_tasks:
            linked_info = []
            if self.tag.linked_projects:
                linked_info.append(f"{len(self.tag.linked_projects)} projects")
            if self.tag.linked_tasks:
                linked_info.append(f"{len(self.tag.linked_tasks)} tasks")

            linked_label = QLabel(f"({', '.join(linked_info)})")
            linked_label.setFont(QFont("Arial", 8))
            linked_label.setStyleSheet("color: #007bff;")
            layout.addWidget(linked_label)

        # Popularity indicator
        if self.tag.usage_count > 5:
            popularity_frame = QFrame()
            popularity_frame.setFixedSize(8, 8)
            popularity_frame.setStyleSheet(
                "background-color: #28a745; border-radius: 4px;"
            )
            layout.addWidget(popularity_frame)

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            # Check if Ctrl is pressed for info dialog (future feature)
            if event.modifiers() & Qt.ControlModifier:
                # Could add tag info dialog here in the future
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle mouse double-click events."""
        if event.button() == Qt.LeftButton:
            # Emit edit signal for the tag
            if hasattr(self.parent(), "parent") and self.parent().parent():
                # Find the TagListWidget parent
                list_widget = self.parent().parent()
                if hasattr(list_widget, "tag_edit_requested"):
                    list_widget.tag_edit_requested.emit(self.tag)
            event.accept()
            return

        super().mouseDoubleClickEvent(event)


class TagListWidget(QListWidget):
    """
    Custom list widget for displaying tags with rich information.

    Provides context menu for editing and deleting tags,
    and visual indicators for tag usage and popularity.
    """

    tag_edit_requested = Signal(Tag)
    tag_delete_requested = Signal(Tag)
    tag_selected = Signal(Tag)

    def __init__(self, parent=None):
        """Initialize the tag list widget."""
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        self.setAlternatingRowColors(True)
        self.setSpacing(2)
        self.itemClicked.connect(self.on_item_clicked)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def add_tag(self, tag: Tag, search_query: str = ""):
        """Add a tag to the list."""
        item = QListWidgetItem(self)
        item_widget = TagItemWidget(tag, search_query)
        item.setSizeHint(item_widget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, item_widget)
        item.setData(Qt.UserRole, tag)

    def update_tags(self, tags: List[Tag], search_query: str = ""):
        """Update the list with new tags."""
        self.clear()
        for tag in tags:
            self.add_tag(tag, search_query)

    def get_selected_tag(self) -> Optional[Tag]:
        """Get the currently selected tag."""
        current_item = self.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole)
        return None

    def on_item_clicked(self, item: QListWidgetItem):
        """Handle item click."""
        tag = item.data(Qt.UserRole)
        if tag:
            self.tag_selected.emit(tag)

    def show_context_menu(self, position):
        """Show context menu for the clicked item."""
        item = self.itemAt(position)
        if not item:
            return

        tag = item.data(Qt.UserRole)
        if not tag:
            return

        menu = QMenu(self)

        edit_action = menu.addAction("Edit Tag")
        edit_action.triggered.connect(lambda: self.tag_edit_requested.emit(tag))

        delete_action = menu.addAction("Delete Tag")
        delete_action.triggered.connect(lambda: self.confirm_delete_tag(tag))

        menu.exec_(self.mapToGlobal(position))

    def confirm_delete_tag(self, tag: Tag):
        """Confirm tag deletion."""
        reply = QMessageBox.question(
            self,
            "Delete Tag",
            f"Are you sure you want to delete tag '{tag.name}'?\n\n"
            f"This will remove the tag from {tag.usage_count} items.\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.tag_delete_requested.emit(tag)
