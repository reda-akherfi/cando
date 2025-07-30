"""
Tag selection dialog for the Cando application.

This module provides a dialog for selecting existing tags or creating new ones
with search functionality.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QMessageBox,
    QFrame,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from app.ui.base_dialog import BaseDialog
from app.ui.tag_dialog import TagDialog


class TagSelectionDialog(BaseDialog):
    """
    Dialog for selecting existing tags or creating new ones.

    Provides search functionality and allows creation of new tags
    if the search doesn't match exactly.
    """

    tag_selected = Signal(str)  # Signal emitted when a tag is selected

    def __init__(self, existing_tags: list, parent=None):
        """
        Initialize the tag selection dialog.

        Args:
            existing_tags: List of existing tag names
            parent: Parent widget
        """
        super().__init__(parent)
        self.existing_tags = existing_tags
        self.selected_tag = None
        self.setup_ui()
        self.setup_tag_selection_sizing()

    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Select or Create Tag")

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Search section
        search_label = QLabel("Search existing tags:")
        search_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to search tags...")
        self.search_input.textChanged.connect(self.on_search_changed)
        layout.addWidget(self.search_input)

        # Tags list
        list_label = QLabel("Available tags:")
        list_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(list_label)

        self.tags_list = QListWidget()
        self.tags_list.setMaximumHeight(200)
        self.tags_list.itemDoubleClicked.connect(self.on_tag_double_clicked)
        layout.addWidget(self.tags_list)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.create_new_button = QPushButton("Create New Tag")
        self.create_new_button.clicked.connect(self.create_new_tag)

        self.select_button = QPushButton("Select")
        self.select_button.clicked.connect(self.select_current_tag)
        self.select_button.setEnabled(False)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.create_new_button)
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # Populate the list
        self.populate_tags_list()

    def setup_tag_selection_sizing(self):
        """Set up custom sizing for the tag selection dialog."""
        # Override the base dialog sizing with more appropriate dimensions
        self.setFixedSize(450, 400)  # Compact size suitable for tag selection

        # Center the dialog on screen
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)

    def populate_tags_list(self, filter_text=""):
        """Populate the tags list with filtered results."""
        self.tags_list.clear()

        # Filter tags based on search text
        filtered_tags = []
        if filter_text:
            filter_lower = filter_text.lower()
            for tag in self.existing_tags:
                if filter_lower in tag.lower():
                    filtered_tags.append(tag)
        else:
            filtered_tags = self.existing_tags

        # Add filtered tags to list
        for tag in sorted(filtered_tags):
            item = QListWidgetItem(tag)
            self.tags_list.addItem(item)

    def on_search_changed(self):
        """Handle search text changes."""
        search_text = self.search_input.text().strip()
        self.populate_tags_list(search_text)

        # Enable/disable select button based on whether there's a selection
        self.select_button.setEnabled(self.tags_list.currentItem() is not None)

    def on_tag_double_clicked(self, item):
        """Handle double-click on a tag item."""
        self.selected_tag = item.text()
        self.accept()

    def select_current_tag(self):
        """Select the currently highlighted tag."""
        current_item = self.tags_list.currentItem()
        if current_item:
            self.selected_tag = current_item.text()
            self.accept()

    def create_new_tag(self):
        """Create a new tag using the TagDialog."""
        # Get the search text as the default tag name
        default_name = self.search_input.text().strip()

        # Create tag dialog
        dialog = TagDialog(tag_name=default_name, parent=self)
        if dialog.exec() == QDialog.Accepted:
            tag_data = dialog.get_tag_data()
            if tag_data["name"]:
                # Check if tag already exists
                if tag_data["name"] in self.existing_tags:
                    QMessageBox.warning(
                        self, "Tag Exists", f"Tag '{tag_data['name']}' already exists."
                    )
                    return

                # Add the new tag to the database
                # Find the main window to access the database service
                main_window = self.parent()
                while main_window and not hasattr(main_window, "db_service"):
                    main_window = main_window.parent()

                if main_window and hasattr(main_window, "db_service"):
                    if main_window.db_service.add_tag(
                        tag_data["name"], tag_data["color"], tag_data["description"]
                    ):
                        # Add to existing tags list
                        self.existing_tags.append(tag_data["name"])

                        # Select the newly created tag
                        self.selected_tag = tag_data["name"]
                        self.accept()
                    else:
                        QMessageBox.warning(
                            self, "Error", f"Could not create tag '{tag_data['name']}'."
                        )

    def get_selected_tag(self):
        """Get the selected tag name."""
        return self.selected_tag
