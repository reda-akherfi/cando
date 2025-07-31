"""
Theme configuration system for the Cando application.

This module provides a comprehensive theming system that allows users to
customize all colors in the application with visual color pickers.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QGridLayout,
    QColorDialog,
    QFrame,
    QScrollArea,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QFormLayout,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette, QFont
from typing import Dict, Any
import json


class ColorPickerButton(QPushButton):
    """A button that opens a color picker dialog."""

    color_changed = Signal(str)  # Emits the new color as hex string

    def __init__(self, initial_color: str = "#000000", parent=None):
        super().__init__(parent)
        self.current_color = initial_color
        self.setFixedSize(60, 30)
        self.clicked.connect(self.open_color_dialog)
        self.update_display()

    def open_color_dialog(self):
        """Open the color picker dialog."""
        color = QColorDialog.getColor(QColor(self.current_color), self)
        if color.isValid():
            self.current_color = color.name()
            self.update_display()
            self.color_changed.emit(self.current_color)

    def update_display(self):
        """Update the button appearance to show the current color."""
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.current_color};
                border: 2px solid #666666;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border: 2px solid #999999;
            }}
        """
        )

    def set_color(self, color: str):
        """Set the color programmatically."""
        self.current_color = color
        self.update_display()


class ThemeConfigWidget(QWidget):
    """Widget for configuring application themes with visual color pickers."""

    theme_changed = Signal(dict)  # Emits the new theme configuration

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_theme = self.get_default_theme()
        self.setup_ui()
        self.load_current_theme()

    def get_default_theme(self) -> Dict[str, Any]:
        """Get the default theme configuration."""
        return {
            "name": "Custom Theme",
            "colors": {
                # Background colors
                "window": "#1e1e1e",
                "base": "#2d2d30",
                "alternate_base": "#252526",
                "tool_tip_base": "#2d2d30",
                "tool_tip_text": "#cccccc",
                # Text colors
                "text": "#cccccc",
                "bright_text": "#ffffff",
                "button_text": "#cccccc",
                "link": "#0078d4",
                "link_visited": "#68217a",
                # Button colors
                "button": "#3c3c3c",
                "light": "#4c4c4c",
                "midlight": "#3c3c3c",
                "mid": "#2d2d30",
                "dark": "#1e1e1e",
                "shadow": "#0f0f0f",
                # Highlight colors
                "highlight": "#0078d4",
                "highlighted_text": "#ffffff",
                # Chart colors
                "chart_background": "#1e1e1e",
                "chart_text": "#cccccc",
                "chart_grid": "#404040",
                "chart_primary": "#0078d4",
                "chart_secondary": "#68217a",
                "chart_success": "#107c10",
                "chart_warning": "#ff8c00",
                "chart_error": "#e81123",
                # Priority colors
                "priority_low": "#00ff00",
                "priority_medium": "#ffff00",
                "priority_high": "#ff8800",
                "priority_critical": "#ff0000",
                # Status colors
                "status_active": "#00ff00",
                "status_in_progress": "#00aaff",
                "status_on_hold": "#ffff00",
                "status_completed": "#00ff00",
                "status_cancelled": "#ff0000",
            },
            "fonts": {
                "base_size": 14,
                "title_size": 18,
                "subtitle_size": 16,
                "font_family": "Segoe UI",
            },
            "spacing": {"padding": 8, "margin": 4, "border_radius": 4},
        }

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Create scroll area for the content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # Theme presets
        self.setup_presets_section(content_layout)

        # Background colors
        self.setup_background_colors_section(content_layout)

        # Text colors
        self.setup_text_colors_section(content_layout)

        # Button colors
        self.setup_button_colors_section(content_layout)

        # Highlight colors
        self.setup_highlight_colors_section(content_layout)

        # Chart colors
        self.setup_chart_colors_section(content_layout)

        # Priority colors
        self.setup_priority_colors_section(content_layout)

        # Status colors
        self.setup_status_colors_section(content_layout)

        # Font settings
        self.setup_font_settings_section(content_layout)

        # Spacing settings
        self.setup_spacing_settings_section(content_layout)

        # Action buttons
        self.setup_action_buttons(content_layout)

        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

    def setup_presets_section(self, parent_layout):
        """Set up the theme presets section."""
        group = QGroupBox("Theme Presets")
        layout = QVBoxLayout(group)

        preset_layout = QHBoxLayout()

        # Preset selector
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(
            [
                "Custom Theme",
                "Dark Theme",
                "Light Theme",
                "High Contrast Dark",
                "High Contrast Light",
            ]
        )
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)

        # Apply preset button
        apply_preset_btn = QPushButton("Apply Preset")
        apply_preset_btn.clicked.connect(self.apply_selected_preset)

        preset_layout.addWidget(QLabel("Select Preset:"))
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addWidget(apply_preset_btn)
        preset_layout.addStretch()

        layout.addLayout(preset_layout)
        parent_layout.addWidget(group)

    def setup_background_colors_section(self, parent_layout):
        """Set up the background colors section."""
        group = QGroupBox("Background Colors")
        layout = QGridLayout(group)

        self.background_pickers = {}
        colors = [
            ("window", "Main Window"),
            ("base", "Base Background"),
            ("alternate_base", "Alternate Base"),
            ("tool_tip_base", "Tooltip Background"),
        ]

        for i, (key, label) in enumerate(colors):
            row = i // 2
            col = i % 2 * 2

            layout.addWidget(QLabel(label), row, col)
            picker = ColorPickerButton(self.current_theme["colors"][key])
            picker.color_changed.connect(
                lambda color, k=key: self.on_color_changed(k, color)
            )
            self.background_pickers[key] = picker
            layout.addWidget(picker, row, col + 1)

        parent_layout.addWidget(group)

    def setup_text_colors_section(self, parent_layout):
        """Set up the text colors section."""
        group = QGroupBox("Text Colors")
        layout = QGridLayout(group)

        self.text_pickers = {}
        colors = [
            ("text", "Main Text"),
            ("bright_text", "Bright Text"),
            ("button_text", "Button Text"),
            ("link", "Links"),
            ("link_visited", "Visited Links"),
            ("tool_tip_text", "Tooltip Text"),
        ]

        for i, (key, label) in enumerate(colors):
            row = i // 2
            col = i % 2 * 2

            layout.addWidget(QLabel(label), row, col)
            picker = ColorPickerButton(self.current_theme["colors"][key])
            picker.color_changed.connect(
                lambda color, k=key: self.on_color_changed(k, color)
            )
            self.text_pickers[key] = picker
            layout.addWidget(picker, row, col + 1)

        parent_layout.addWidget(group)

    def setup_button_colors_section(self, parent_layout):
        """Set up the button colors section."""
        group = QGroupBox("Button Colors")
        layout = QGridLayout(group)

        self.button_pickers = {}
        colors = [
            ("button", "Button Background"),
            ("light", "Light Button"),
            ("midlight", "Midlight Button"),
            ("mid", "Mid Button"),
            ("dark", "Dark Button"),
            ("shadow", "Shadow"),
        ]

        for i, (key, label) in enumerate(colors):
            row = i // 2
            col = i % 2 * 2

            layout.addWidget(QLabel(label), row, col)
            picker = ColorPickerButton(self.current_theme["colors"][key])
            picker.color_changed.connect(
                lambda color, k=key: self.on_color_changed(k, color)
            )
            self.button_pickers[key] = picker
            layout.addWidget(picker, row, col + 1)

        parent_layout.addWidget(group)

    def setup_highlight_colors_section(self, parent_layout):
        """Set up the highlight colors section."""
        group = QGroupBox("Highlight Colors")
        layout = QGridLayout(group)

        self.highlight_pickers = {}
        colors = [
            ("highlight", "Selection Highlight"),
            ("highlighted_text", "Highlighted Text"),
        ]

        for i, (key, label) in enumerate(colors):
            row = i // 2
            col = i % 2 * 2

            layout.addWidget(QLabel(label), row, col)
            picker = ColorPickerButton(self.current_theme["colors"][key])
            picker.color_changed.connect(
                lambda color, k=key: self.on_color_changed(k, color)
            )
            self.highlight_pickers[key] = picker
            layout.addWidget(picker, row, col + 1)

        parent_layout.addWidget(group)

    def setup_chart_colors_section(self, parent_layout):
        """Set up the chart colors section."""
        group = QGroupBox("Chart Colors")
        layout = QGridLayout(group)

        self.chart_pickers = {}
        colors = [
            ("chart_background", "Chart Background"),
            ("chart_text", "Chart Text"),
            ("chart_grid", "Chart Grid"),
            ("chart_primary", "Primary Color"),
            ("chart_secondary", "Secondary Color"),
            ("chart_success", "Success Color"),
            ("chart_warning", "Warning Color"),
            ("chart_error", "Error Color"),
        ]

        for i, (key, label) in enumerate(colors):
            row = i // 2
            col = i % 2 * 2

            layout.addWidget(QLabel(label), row, col)
            picker = ColorPickerButton(self.current_theme["colors"][key])
            picker.color_changed.connect(
                lambda color, k=key: self.on_color_changed(k, color)
            )
            self.chart_pickers[key] = picker
            layout.addWidget(picker, row, col + 1)

        parent_layout.addWidget(group)

    def setup_priority_colors_section(self, parent_layout):
        """Set up the priority colors section."""
        group = QGroupBox("Priority Colors")
        layout = QGridLayout(group)

        self.priority_pickers = {}
        colors = [
            ("priority_low", "Low Priority"),
            ("priority_medium", "Medium Priority"),
            ("priority_high", "High Priority"),
            ("priority_critical", "Critical Priority"),
        ]

        for i, (key, label) in enumerate(colors):
            row = i // 2
            col = i % 2 * 2

            layout.addWidget(QLabel(label), row, col)
            picker = ColorPickerButton(self.current_theme["colors"][key])
            picker.color_changed.connect(
                lambda color, k=key: self.on_color_changed(k, color)
            )
            self.priority_pickers[key] = picker
            layout.addWidget(picker, row, col + 1)

        parent_layout.addWidget(group)

    def setup_status_colors_section(self, parent_layout):
        """Set up the status colors section."""
        group = QGroupBox("Status Colors")
        layout = QGridLayout(group)

        self.status_pickers = {}
        colors = [
            ("status_active", "Active"),
            ("status_in_progress", "In Progress"),
            ("status_on_hold", "On Hold"),
            ("status_completed", "Completed"),
            ("status_cancelled", "Cancelled"),
        ]

        for i, (key, label) in enumerate(colors):
            row = i // 2
            col = i % 2 * 2

            layout.addWidget(QLabel(label), row, col)
            picker = ColorPickerButton(self.current_theme["colors"][key])
            picker.color_changed.connect(
                lambda color, k=key: self.on_color_changed(k, color)
            )
            self.status_pickers[key] = picker
            layout.addWidget(picker, row, col + 1)

        parent_layout.addWidget(group)

    def setup_font_settings_section(self, parent_layout):
        """Set up the font settings section."""
        group = QGroupBox("Font Settings")
        layout = QFormLayout(group)

        # Base font size
        self.base_font_size_spin = QSpinBox()
        self.base_font_size_spin.setRange(8, 24)
        self.base_font_size_spin.setValue(self.current_theme["fonts"]["base_size"])
        self.base_font_size_spin.valueChanged.connect(self.on_font_setting_changed)
        layout.addRow("Base Font Size:", self.base_font_size_spin)

        # Title font size
        self.title_font_size_spin = QSpinBox()
        self.title_font_size_spin.setRange(12, 32)
        self.title_font_size_spin.setValue(self.current_theme["fonts"]["title_size"])
        self.title_font_size_spin.valueChanged.connect(self.on_font_setting_changed)
        layout.addRow("Title Font Size:", self.title_font_size_spin)

        # Subtitle font size
        self.subtitle_font_size_spin = QSpinBox()
        self.subtitle_font_size_spin.setRange(10, 28)
        self.subtitle_font_size_spin.setValue(
            self.current_theme["fonts"]["subtitle_size"]
        )
        self.subtitle_font_size_spin.valueChanged.connect(self.on_font_setting_changed)
        layout.addRow("Subtitle Font Size:", self.subtitle_font_size_spin)

        parent_layout.addWidget(group)

    def setup_spacing_settings_section(self, parent_layout):
        """Set up the spacing settings section."""
        group = QGroupBox("Spacing Settings")
        layout = QFormLayout(group)

        # Padding
        self.padding_spin = QSpinBox()
        self.padding_spin.setRange(0, 20)
        self.padding_spin.setValue(self.current_theme["spacing"]["padding"])
        self.padding_spin.valueChanged.connect(self.on_spacing_setting_changed)
        layout.addRow("Padding:", self.padding_spin)

        # Margin
        self.margin_spin = QSpinBox()
        self.margin_spin.setRange(0, 20)
        self.margin_spin.setValue(self.current_theme["spacing"]["margin"])
        self.margin_spin.valueChanged.connect(self.on_spacing_setting_changed)
        layout.addRow("Margin:", self.margin_spin)

        # Border radius
        self.border_radius_spin = QSpinBox()
        self.border_radius_spin.setRange(0, 20)
        self.border_radius_spin.setValue(self.current_theme["spacing"]["border_radius"])
        self.border_radius_spin.valueChanged.connect(self.on_spacing_setting_changed)
        layout.addRow("Border Radius:", self.border_radius_spin)

        parent_layout.addWidget(group)

    def setup_action_buttons(self, parent_layout):
        """Set up the action buttons."""
        button_layout = QHBoxLayout()

        # Save theme button
        save_btn = QPushButton("Save Theme")
        save_btn.clicked.connect(self.save_theme)
        button_layout.addWidget(save_btn)

        # Reset to default button
        reset_btn = QPushButton("Reset to Default")
        reset_btn.clicked.connect(self.reset_to_default)
        button_layout.addWidget(reset_btn)

        # Apply theme button
        apply_btn = QPushButton("Apply Theme")
        apply_btn.clicked.connect(self.apply_theme)
        button_layout.addWidget(apply_btn)

        button_layout.addStretch()
        parent_layout.addLayout(button_layout)

    def on_color_changed(self, key: str, color: str):
        """Handle color change from picker."""
        self.current_theme["colors"][key] = color

    def on_font_setting_changed(self):
        """Handle font setting change."""
        self.current_theme["fonts"]["base_size"] = self.base_font_size_spin.value()
        self.current_theme["fonts"]["title_size"] = self.title_font_size_spin.value()
        self.current_theme["fonts"][
            "subtitle_size"
        ] = self.subtitle_font_size_spin.value()

    def on_spacing_setting_changed(self):
        """Handle spacing setting change."""
        self.current_theme["spacing"]["padding"] = self.padding_spin.value()
        self.current_theme["spacing"]["margin"] = self.margin_spin.value()
        self.current_theme["spacing"]["border_radius"] = self.border_radius_spin.value()

    def on_preset_changed(self, preset_name: str):
        """Handle preset selection change."""
        # This will be handled when the apply preset button is clicked
        pass

    def apply_selected_preset(self):
        """Apply the selected preset."""
        preset_name = self.preset_combo.currentText()

        if preset_name == "Dark Theme":
            self.load_dark_preset()
        elif preset_name == "Light Theme":
            self.load_light_preset()
        elif preset_name == "High Contrast Dark":
            self.load_high_contrast_dark_preset()
        elif preset_name == "High Contrast Light":
            self.load_high_contrast_light_preset()

        self.update_all_pickers()

    def load_dark_preset(self):
        """Load the dark theme preset."""
        self.current_theme["colors"].update(
            {
                "window": "#1e1e1e",
                "base": "#2d2d30",
                "alternate_base": "#252526",
                "tool_tip_base": "#2d2d30",
                "tool_tip_text": "#cccccc",
                "text": "#cccccc",
                "bright_text": "#ffffff",
                "button_text": "#cccccc",
                "link": "#0078d4",
                "link_visited": "#68217a",
                "button": "#3c3c3c",
                "light": "#4c4c4c",
                "midlight": "#3c3c3c",
                "mid": "#2d2d30",
                "dark": "#1e1e1e",
                "shadow": "#0f0f0f",
                "highlight": "#0078d4",
                "highlighted_text": "#ffffff",
                "chart_background": "#1e1e1e",
                "chart_text": "#cccccc",
                "chart_grid": "#404040",
            }
        )

    def load_light_preset(self):
        """Load the light theme preset."""
        self.current_theme["colors"].update(
            {
                "window": "#f5f5f5",
                "base": "#ffffff",
                "alternate_base": "#f0f0f0",
                "tool_tip_base": "#ffffff",
                "tool_tip_text": "#333333",
                "text": "#333333",
                "bright_text": "#000000",
                "button_text": "#333333",
                "link": "#0066cc",
                "link_visited": "#660099",
                "button": "#e1e1e1",
                "light": "#f5f5f5",
                "midlight": "#e8e8e8",
                "mid": "#d4d4d4",
                "dark": "#a0a0a0",
                "shadow": "#808080",
                "highlight": "#0078d4",
                "highlighted_text": "#ffffff",
                "chart_background": "#ffffff",
                "chart_text": "#333333",
                "chart_grid": "#e0e0e0",
            }
        )

    def load_high_contrast_dark_preset(self):
        """Load the high contrast dark preset."""
        self.current_theme["colors"].update(
            {
                "window": "#0a0a0a",
                "base": "#1a1a1a",
                "alternate_base": "#0f0f0f",
                "tool_tip_base": "#1a1a1a",
                "tool_tip_text": "#ffffff",
                "text": "#ffffff",
                "bright_text": "#ffffff",
                "button_text": "#ffffff",
                "link": "#00aaff",
                "link_visited": "#ff00ff",
                "button": "#444444",
                "light": "#666666",
                "midlight": "#444444",
                "mid": "#333333",
                "dark": "#222222",
                "shadow": "#111111",
                "highlight": "#00aaff",
                "highlighted_text": "#000000",
                "chart_background": "#0a0a0a",
                "chart_text": "#ffffff",
                "chart_grid": "#444444",
            }
        )

    def load_high_contrast_light_preset(self):
        """Load the high contrast light preset."""
        self.current_theme["colors"].update(
            {
                "window": "#ffffff",
                "base": "#ffffff",
                "alternate_base": "#f0f0f0",
                "tool_tip_base": "#ffffff",
                "tool_tip_text": "#000000",
                "text": "#000000",
                "bright_text": "#000000",
                "button_text": "#000000",
                "link": "#0000ff",
                "link_visited": "#800080",
                "button": "#cccccc",
                "light": "#e6e6e6",
                "midlight": "#cccccc",
                "mid": "#999999",
                "dark": "#666666",
                "shadow": "#333333",
                "highlight": "#0000ff",
                "highlighted_text": "#ffffff",
                "chart_background": "#ffffff",
                "chart_text": "#000000",
                "chart_grid": "#999999",
            }
        )

    def update_all_pickers(self):
        """Update all color pickers with current theme values."""
        all_pickers = {
            **self.background_pickers,
            **self.text_pickers,
            **self.button_pickers,
            **self.highlight_pickers,
            **self.chart_pickers,
            **self.priority_pickers,
            **self.status_pickers,
        }

        for key, picker in all_pickers.items():
            if key in self.current_theme["colors"]:
                picker.set_color(self.current_theme["colors"][key])

    def load_current_theme(self):
        """Load the current theme into the UI."""
        self.update_all_pickers()

        # Update font settings
        self.base_font_size_spin.setValue(self.current_theme["fonts"]["base_size"])
        self.title_font_size_spin.setValue(self.current_theme["fonts"]["title_size"])
        self.subtitle_font_size_spin.setValue(
            self.current_theme["fonts"]["subtitle_size"]
        )

        # Update spacing settings
        self.padding_spin.setValue(self.current_theme["spacing"]["padding"])
        self.margin_spin.setValue(self.current_theme["spacing"]["margin"])
        self.border_radius_spin.setValue(self.current_theme["spacing"]["border_radius"])

    def save_theme(self):
        """Save the current theme configuration."""
        # This will be implemented to save to database
        self.theme_changed.emit(self.current_theme)

    def reset_to_default(self):
        """Reset to the default theme."""
        self.current_theme = self.get_default_theme()
        self.load_current_theme()

    def apply_theme(self):
        """Apply the current theme to the application."""
        self.theme_changed.emit(self.current_theme)

    def get_theme_config(self) -> Dict[str, Any]:
        """Get the current theme configuration."""
        return self.current_theme

    def set_theme_config(self, config: Dict[str, Any]):
        """Set the theme configuration."""
        self.current_theme = config
        self.load_current_theme()
