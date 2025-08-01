"""
Checklist filter widget for the Cando application.

This module provides a custom filter widget that allows multiple selections
with a dropdown modal interface and compact display of selected items.
"""

from typing import List, Set, Callable
from functools import partial
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QCheckBox,
    QScrollArea,
    QSizePolicy,
    QDialog,
    QApplication,
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QFont


class ChecklistFilterDialog(QDialog):
    """Modal dialog for checklist filter selection."""

    def __init__(
        self, title: str, items: List[str], selected_items: Set[str], parent=None
    ):
        super().__init__(parent)
        self.title = title
        self.items = items
        self.selected_items = selected_items.copy()
        self.result_items = set()
        self.checkboxes = {}  # Store checkboxes by item name
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle(f"Select {self.title}")
        self.setModal(True)
        self.setFixedSize(300, 400)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Title
        title_label = QLabel(f"Select {self.title}:")
        title_label.setFont(QFont("Arial", 10, QFont.Bold))
        title_label.setStyleSheet("color: #cccccc;")
        layout.addWidget(title_label)

        # Scroll area for checkboxes
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(
            """
            QScrollArea {
                border: 1px solid #4c4c4c;
                border-radius: 4px;
                background-color: #2d2d30;
            }
        """
        )

        # Container for checkboxes
        checkbox_container = QWidget()
        checkbox_layout = QVBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(8, 8, 8, 8)
        checkbox_layout.setSpacing(4)

        # Add checkboxes for each item
        for item in self.items:
            checkbox = QCheckBox(item)
            # Store the item as a property on the checkbox for easy access
            checkbox.item_name = item
            # Set the initial state before connecting the signal to avoid triggering it
            checkbox.setChecked(item in self.selected_items)
            checkbox.stateChanged.connect(self.on_checkbox_changed)
            # Store the checkbox for later access
            self.checkboxes[item] = checkbox
            checkbox.setStyleSheet(
                """
                QCheckBox {
                    color: #cccccc;
                    font-size: 10px;
                    spacing: 6px;
                }
                QCheckBox::indicator {
                    width: 14px;
                    height: 14px;
                    border: 1px solid #4c4c4c;
                    border-radius: 2px;
                    background-color: #2d2d30;
                }
                QCheckBox::indicator:checked {
                    background-color: #0078d4;
                    border-color: #0078d4;
                }
                QCheckBox::indicator:hover {
                    border-color: #0078d4;
                }
            """
            )
            checkbox_layout.addWidget(checkbox)

        scroll_area.setWidget(checkbox_container)
        layout.addWidget(scroll_area)

        # Action buttons
        button_layout = QHBoxLayout()

        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all)
        select_all_btn.setStyleSheet(
            """
            QPushButton {
                border: 1px solid #4c4c4c;
                border-radius: 3px;
                background-color: #3c3c3c;
                color: #cccccc;
                font-size: 9px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
        """
        )

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_selection)
        clear_btn.setStyleSheet(
            """
            QPushButton {
                border: 1px solid #4c4c4c;
                border-radius: 3px;
                background-color: #3c3c3c;
                color: #cccccc;
                font-size: 9px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
        """
        )

        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(clear_btn)
        button_layout.addStretch()

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setStyleSheet(
            """
            QPushButton {
                border: 1px solid #0078d4;
                border-radius: 3px;
                background-color: #0078d4;
                color: white;
                font-size: 9px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """
        )

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(
            """
            QPushButton {
                border: 1px solid #4c4c4c;
                border-radius: 3px;
                background-color: #3c3c3c;
                color: #cccccc;
                font-size: 9px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
        """
        )

        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        # Set dialog styling
        self.setStyleSheet(
            """
            QDialog {
                background-color: #1e1e1e;
                border: 1px solid #4c4c4c;
                border-radius: 6px;
            }
        """
        )

    def on_checkbox_changed(self, state: int):
        """Handle checkbox state changes."""
        # Get the item name from the sender checkbox
        checkbox = self.sender()
        if checkbox and hasattr(checkbox, "item_name"):
            item = checkbox.item_name
            # Get the actual current state of the checkbox
            actual_state = checkbox.isChecked()
            print(
                f"DEBUG: Checkbox '{item}' signal state: {state}, actual state: {actual_state}"
            )

            # Use the actual checkbox state instead of the signal parameter
            if actual_state:
                self.selected_items.add(item)
                print(
                    f"DEBUG: Dialog - added {item}, selected_items now: {self.selected_items}"
                )
            else:
                self.selected_items.discard(item)
                print(
                    f"DEBUG: Dialog - removed {item}, selected_items now: {self.selected_items}"
                )

    def select_all(self):
        """Select all items."""
        self.selected_items = set(self.items)
        # Update all checkboxes
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if isinstance(item.widget(), QScrollArea):
                scroll_widget = item.widget().widget()
                for j in range(scroll_widget.layout().count()):
                    checkbox_item = scroll_widget.layout().itemAt(j)
                    if isinstance(checkbox_item.widget(), QCheckBox):
                        checkbox_item.widget().setChecked(True)
                break

    def clear_selection(self):
        """Clear all selections."""
        # When clearing, we want to show all items, so return empty list
        self.selected_items.clear()
        # Update all checkboxes to unchecked
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if isinstance(item.widget(), QScrollArea):
                scroll_widget = item.widget().widget()
                for j in range(scroll_widget.layout().count()):
                    checkbox_item = scroll_widget.layout().itemAt(j)
                    if isinstance(checkbox_item.widget(), QCheckBox):
                        checkbox_item.widget().setChecked(False)
                break

    def get_selected_items(self) -> List[str]:
        """Get the selected items."""
        result = list(self.selected_items)
        print(f"DEBUG: Dialog get_selected_items returning: {result}")
        return result


class ChecklistFilterWidget(QWidget):
    """
    Custom filter widget that allows multiple selections.

    Displays selected items in a compact format and provides a dropdown
    modal with checkboxes for selection.
    """

    selection_changed = Signal(list)  # Emits list of selected items

    def __init__(self, title: str = "Filter", parent=None):
        """Initialize the checklist filter widget."""
        super().__init__(parent)
        self.title = title
        self.items = []
        self.selected_items = set()
        self.on_selection_changed_callback = None
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Title label
        self.title_label = QLabel(self.title + ":")
        self.title_label.setFont(QFont("Arial", 9))
        self.title_label.setStyleSheet("color: #cccccc;")
        layout.addWidget(self.title_label)

        # Selected items display (clickable) with integrated dropdown arrow
        self.selected_display = QPushButton("All ▼")
        self.selected_display.setFont(QFont("Arial", 9))
        self.selected_display.clicked.connect(self.show_dropdown)
        self.selected_display.setStyleSheet(
            """
            QPushButton {
                color: #cccccc;
                background-color: #2d2d30;
                border: 1px solid #4c4c4c;
                border-radius: 3px;
                padding: 4px 8px;
                min-height: 16px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #3c3c3c;
                border-color: #0078d4;
            }
        """
        )
        layout.addWidget(self.selected_display)

    def set_items(self, items: List[str]):
        """Set the available items for selection."""
        self.items = items
        # Start with all items selected (show "All" by default)
        self.selected_items = set(items)
        self.update_display()

        # If no items, disable the widget
        if not items:
            self.setEnabled(False)
        else:
            self.setEnabled(True)

    def set_selected_items(self, items: List[str]):
        """Set the selected items."""
        self.selected_items = set(items)
        self.update_display()

    def get_selected_items(self) -> List[str]:
        """Get the currently selected items."""
        # If all items are selected OR no items are selected, return empty list to indicate "show all"
        if len(self.selected_items) == len(self.items) or len(self.selected_items) == 0:
            print(
                f"DEBUG: {self.title} - {'all' if len(self.selected_items) == len(self.items) else 'no'} items selected, returning []"
            )
            return []
        result = list(self.selected_items)
        print(f"DEBUG: {self.title} - returning selected items: {result}")
        return result

    def update_display(self):
        """Update the display of selected items."""
        if not self.selected_items or len(self.selected_items) == len(self.items):
            self.selected_display.setText("All ▼")
        elif len(self.selected_items) == 1:
            self.selected_display.setText(f"{list(self.selected_items)[0]} ▼")
        else:
            # Show first few items with count
            items_list = list(self.selected_items)
            if len(items_list) <= 2:
                self.selected_display.setText(f"{', '.join(items_list)} ▼")
            else:
                self.selected_display.setText(
                    f"{items_list[0]}, {items_list[1]} +{len(items_list)-2} ▼"
                )

    def show_dropdown(self):
        """Show the dropdown modal."""
        if not self.items:
            return

        # Position the dialog relative to the widget
        global_pos = self.mapToGlobal(self.rect().bottomLeft())

        # Create dialog with current selection state
        # If we're showing "All", pass all items as selected to the dialog
        if len(self.selected_items) == len(self.items) or len(self.selected_items) == 0:
            dialog_selected = set(self.items)  # Start with all selected
        else:
            dialog_selected = self.selected_items.copy()

        dialog = ChecklistFilterDialog(self.title, self.items, dialog_selected, self)

        # Adjust position to keep dialog on screen
        screen = QApplication.primaryScreen().geometry()
        dialog_width = dialog.width()
        dialog_height = dialog.height()

        x = global_pos.x()
        y = global_pos.y() + 2

        # Adjust if dialog would go off screen
        if x + dialog_width > screen.right():
            x = screen.right() - dialog_width - 10
        if y + dialog_height > screen.bottom():
            y = global_pos.y() - dialog_height - 2

        dialog.move(x, y)

        if dialog.exec() == QDialog.Accepted:
            dialog_items = dialog.get_selected_items()
            print(f"DEBUG: Dialog accepted, items from dialog: {dialog_items}")

            # If dialog returns empty list, it means "show all"
            if not dialog_items:
                self.selected_items = set(self.items)  # Select all items
            else:
                self.selected_items = set(dialog_items)

            print(f"DEBUG: Set selected_items to: {self.selected_items}")
            self.update_display()
            final_items = self.get_selected_items()
            print(f"DEBUG: Emitting selection_changed with: {final_items}")
            self.selection_changed.emit(final_items)

            if self.on_selection_changed_callback:
                print(f"DEBUG: Calling callback for {self.title}")
                self.on_selection_changed_callback()

    def set_selection_changed_callback(self, callback: Callable):
        """Set a callback function to be called when selection changes."""
        self.on_selection_changed_callback = callback
