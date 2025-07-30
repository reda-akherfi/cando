"""
Tag dialog for the Cando application.

This module provides a dialog for creating and editing tags
with name, color, and description fields.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QColorDialog,
    QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from app.ui.base_dialog import BaseDialog


class TagDialog(BaseDialog):
    """
    Dialog for creating and editing tags.

    Allows users to set tag name, color, and description.
    """

    def __init__(
        self,
        tag_name: str = "",
        tag_color: str = "#FF5733",
        tag_description: str = "",
        parent=None,
    ):
        """Initialize the tag dialog."""
        super().__init__(parent)
        self.tag_name = tag_name
        self.tag_color = tag_color
        self.tag_description = tag_description
        self.setup_ui()
        self.setup_tag_dialog_sizing()

    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Tag Dialog")

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Tag name
        name_layout = QHBoxLayout()
        name_label = QLabel("Tag Name:")
        name_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.name_input = QLineEdit(self.tag_name)
        self.name_input.setPlaceholderText("Enter tag name...")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Tag color
        color_layout = QHBoxLayout()
        color_label = QLabel("Color:")
        color_label.setFont(QFont("Arial", 10, QFont.Bold))

        # Color preview frame
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(24, 24)
        self.color_preview.setStyleSheet(
            f"background-color: {self.tag_color}; border: 2px solid #ccc; border-radius: 12px;"
        )

        # Color picker button
        self.color_button = QPushButton("Choose Color")
        self.color_button.clicked.connect(self.choose_color)

        color_layout.addWidget(color_label)
        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(self.color_button)
        color_layout.addStretch()
        layout.addLayout(color_layout)

        # Tag description
        desc_label = QLabel("Description:")
        desc_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.desc_input = QTextEdit()
        self.desc_input.setPlainText(self.tag_description)
        self.desc_input.setPlaceholderText("Enter tag description (optional)...")
        self.desc_input.setMaximumHeight(80)
        layout.addWidget(desc_label)
        layout.addWidget(self.desc_input)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        self.save_button.setDefault(True)

        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

    def setup_tag_dialog_sizing(self):
        """Set up custom sizing for the tag dialog."""
        # Override the base dialog sizing with more appropriate dimensions for a tag dialog
        self.setFixedSize(400, 280)  # Compact size suitable for tag editing

        # Center the dialog on screen
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)

    def choose_color(self):
        """Open color picker dialog."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.tag_color = color.name()
            self.color_preview.setStyleSheet(
                f"background-color: {self.tag_color}; border: 2px solid #ccc; border-radius: 12px;"
            )

    def get_tag_data(self):
        """Get the tag data from the dialog."""
        return {
            "name": self.name_input.text().strip(),
            "color": self.tag_color,
            "description": self.desc_input.toPlainText().strip(),
        }
