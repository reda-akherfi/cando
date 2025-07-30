"""
Theme system for the Cando application.

This module provides dark and light mode styling for the entire application,
including PySide6 widgets and matplotlib charts.
"""

from PySide6.QtGui import QPalette, QColor, QFont
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib import rcParams


class LightTheme:
    """Light theme configuration for the Cando application."""

    # Color palette for light theme
    COLORS = {
        # Background colors
        "window": "#f5f5f5",
        "base": "#ffffff",
        "alternate_base": "#f0f0f0",
        "tool_tip_base": "#ffffff",
        "tool_tip_text": "#333333",
        # Text colors
        "text": "#333333",
        "bright_text": "#000000",
        "button_text": "#333333",
        "link": "#0066cc",
        "link_visited": "#660099",
        # Button colors
        "button": "#e1e1e1",
        "light": "#f5f5f5",
        "midlight": "#e8e8e8",
        "mid": "#d4d4d4",
        "dark": "#a0a0a0",
        "shadow": "#808080",
        # Highlight colors
        "highlight": "#0078d4",
        "highlighted_text": "#ffffff",
        # Chart colors
        "chart_background": "#ffffff",
        "chart_text": "#333333",
        "chart_grid": "#e0e0e0",
        "chart_primary": "#0078d4",
        "chart_secondary": "#68217a",
        "chart_success": "#107c10",
        "chart_warning": "#ff8c00",
        "chart_error": "#e81123",
    }

    @classmethod
    def apply_to_application(cls, app: QApplication):
        """Apply light theme to the entire application."""
        cls._apply_pyside6_theme(app)
        cls._apply_matplotlib_theme()

    @classmethod
    def _apply_pyside6_theme(cls, app: QApplication):
        """Apply light theme to PySide6 widgets."""
        palette = QPalette()

        # Set color roles
        palette.setColor(QPalette.Window, QColor(cls.COLORS["window"]))
        palette.setColor(QPalette.WindowText, QColor(cls.COLORS["text"]))
        palette.setColor(QPalette.Base, QColor(cls.COLORS["base"]))
        palette.setColor(QPalette.AlternateBase, QColor(cls.COLORS["alternate_base"]))
        palette.setColor(QPalette.ToolTipBase, QColor(cls.COLORS["tool_tip_base"]))
        palette.setColor(QPalette.ToolTipText, QColor(cls.COLORS["tool_tip_text"]))
        palette.setColor(QPalette.Text, QColor(cls.COLORS["text"]))
        palette.setColor(QPalette.BrightText, QColor(cls.COLORS["bright_text"]))
        palette.setColor(QPalette.Button, QColor(cls.COLORS["button"]))
        palette.setColor(QPalette.ButtonText, QColor(cls.COLORS["button_text"]))
        palette.setColor(QPalette.Link, QColor(cls.COLORS["link"]))
        palette.setColor(QPalette.LinkVisited, QColor(cls.COLORS["link_visited"]))
        palette.setColor(QPalette.Light, QColor(cls.COLORS["light"]))
        palette.setColor(QPalette.Midlight, QColor(cls.COLORS["midlight"]))
        palette.setColor(QPalette.Mid, QColor(cls.COLORS["mid"]))
        palette.setColor(QPalette.Dark, QColor(cls.COLORS["dark"]))
        palette.setColor(QPalette.Shadow, QColor(cls.COLORS["shadow"]))
        palette.setColor(QPalette.Highlight, QColor(cls.COLORS["highlight"]))
        palette.setColor(
            QPalette.HighlightedText, QColor(cls.COLORS["highlighted_text"])
        )

        # Apply palette to application
        app.setPalette(palette)

        # Set application style sheet for additional styling
        app.setStyleSheet(cls._get_stylesheet())

    @classmethod
    def _get_stylesheet(cls) -> str:
        """Get additional CSS stylesheet for light theme."""
        return f"""
        QMainWindow {{
            background-color: {cls.COLORS['window']};
            color: {cls.COLORS['text']};
        }}
        
        QTabWidget::pane {{
            border: 1px solid {cls.COLORS['mid']};
            background-color: {cls.COLORS['base']};
        }}
        
        QTabBar::tab {{
            background-color: {cls.COLORS['button']};
            color: {cls.COLORS['text']};
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {cls.COLORS['highlight']};
            color: {cls.COLORS['highlighted_text']};
        }}
        
        QTabBar::tab:hover {{
            background-color: {cls.COLORS['light']};
        }}
        
        QPushButton {{
            background-color: {cls.COLORS['button']};
            color: {cls.COLORS['text']};
            border: 1px solid {cls.COLORS['mid']};
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }}
        
        QPushButton:hover {{
            background-color: {cls.COLORS['light']};
            border-color: {cls.COLORS['highlight']};
        }}
        
        QPushButton:pressed {{
            background-color: {cls.COLORS['dark']};
        }}
        
        QLabel {{
            color: {cls.COLORS['text']};
            background-color: transparent;
        }}
        
        QListWidget {{
            background-color: {cls.COLORS['base']};
            color: {cls.COLORS['text']};
            border: 1px solid {cls.COLORS['mid']};
            border-radius: 4px;
            padding: 4px;
        }}
        
        QListWidget::item {{
            padding: 6px;
            border-radius: 2px;
            color: {cls.COLORS['text']};
        }}
        
        QListWidget::item:selected {{
            background-color: {cls.COLORS['highlight']};
            color: {cls.COLORS['highlighted_text']};
        }}
        
        QListWidget::item:hover {{
            background-color: {cls.COLORS['light']};
        }}
        
        QScrollBar:vertical {{
            background-color: {cls.COLORS['base']};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {cls.COLORS['mid']};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {cls.COLORS['light']};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QWidget {{
            background-color: {cls.COLORS['base']};
            color: {cls.COLORS['text']};
        }}
        
        QLineEdit {{
            background-color: {cls.COLORS['base']};
            color: {cls.COLORS['text']};
            border: 1px solid {cls.COLORS['mid']};
            border-radius: 4px;
            padding: 4px;
        }}
        
        QComboBox {{
            background-color: {cls.COLORS['base']};
            color: {cls.COLORS['text']};
            border: 1px solid {cls.COLORS['mid']};
            border-radius: 4px;
            padding: 4px;
        }}
        """

    @classmethod
    def _apply_matplotlib_theme(cls):
        """Apply light theme to matplotlib charts."""
        # Set matplotlib style parameters
        rcParams["figure.facecolor"] = cls.COLORS["chart_background"]
        rcParams["axes.facecolor"] = cls.COLORS["chart_background"]
        rcParams["text.color"] = cls.COLORS["chart_text"]
        rcParams["axes.labelcolor"] = cls.COLORS["chart_text"]
        rcParams["xtick.color"] = cls.COLORS["chart_text"]
        rcParams["ytick.color"] = cls.COLORS["chart_text"]
        rcParams["axes.edgecolor"] = cls.COLORS["chart_grid"]
        rcParams["axes.grid"] = True
        rcParams["grid.color"] = cls.COLORS["chart_grid"]
        rcParams["grid.alpha"] = 0.3

    @classmethod
    def get_chart_colors(cls) -> dict:
        """Get chart colors for light theme."""
        return {
            "background": cls.COLORS["chart_background"],
            "text": cls.COLORS["chart_text"],
            "grid": cls.COLORS["chart_grid"],
            "primary": cls.COLORS["chart_primary"],
            "secondary": cls.COLORS["chart_secondary"],
            "success": cls.COLORS["chart_success"],
            "warning": cls.COLORS["chart_warning"],
            "error": cls.COLORS["chart_error"],
        }


class DarkTheme:
    """Dark theme configuration for the Cando application."""

    # Color palette for dark theme
    COLORS = {
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
    }

    @classmethod
    def apply_to_application(cls, app: QApplication):
        """Apply dark theme to the entire application."""
        cls._apply_pyside6_theme(app)
        cls._apply_matplotlib_theme()

    @classmethod
    def _apply_pyside6_theme(cls, app: QApplication):
        """Apply dark theme to PySide6 widgets."""
        palette = QPalette()

        # Set color roles
        palette.setColor(QPalette.Window, QColor(cls.COLORS["window"]))
        palette.setColor(QPalette.WindowText, QColor(cls.COLORS["text"]))
        palette.setColor(QPalette.Base, QColor(cls.COLORS["base"]))
        palette.setColor(QPalette.AlternateBase, QColor(cls.COLORS["alternate_base"]))
        palette.setColor(QPalette.ToolTipBase, QColor(cls.COLORS["tool_tip_base"]))
        palette.setColor(QPalette.ToolTipText, QColor(cls.COLORS["tool_tip_text"]))
        palette.setColor(QPalette.Text, QColor(cls.COLORS["text"]))
        palette.setColor(QPalette.BrightText, QColor(cls.COLORS["bright_text"]))
        palette.setColor(QPalette.Button, QColor(cls.COLORS["button"]))
        palette.setColor(QPalette.ButtonText, QColor(cls.COLORS["button_text"]))
        palette.setColor(QPalette.Link, QColor(cls.COLORS["link"]))
        palette.setColor(QPalette.LinkVisited, QColor(cls.COLORS["link_visited"]))
        palette.setColor(QPalette.Light, QColor(cls.COLORS["light"]))
        palette.setColor(QPalette.Midlight, QColor(cls.COLORS["midlight"]))
        palette.setColor(QPalette.Mid, QColor(cls.COLORS["mid"]))
        palette.setColor(QPalette.Dark, QColor(cls.COLORS["dark"]))
        palette.setColor(QPalette.Shadow, QColor(cls.COLORS["shadow"]))
        palette.setColor(QPalette.Highlight, QColor(cls.COLORS["highlight"]))
        palette.setColor(
            QPalette.HighlightedText, QColor(cls.COLORS["highlighted_text"])
        )

        # Apply palette to application
        app.setPalette(palette)

        # Set application style sheet for additional styling
        app.setStyleSheet(cls._get_stylesheet())

    @classmethod
    def _get_stylesheet(cls) -> str:
        """Get additional CSS stylesheet for dark theme."""
        return f"""
        QMainWindow {{
            background-color: {cls.COLORS['window']};
            color: {cls.COLORS['text']};
        }}
        
        QTabWidget::pane {{
            border: 1px solid {cls.COLORS['mid']};
            background-color: {cls.COLORS['base']};
        }}
        
        QTabBar::tab {{
            background-color: {cls.COLORS['button']};
            color: {cls.COLORS['text']};
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {cls.COLORS['highlight']};
            color: {cls.COLORS['highlighted_text']};
        }}
        
        QTabBar::tab:hover {{
            background-color: {cls.COLORS['light']};
        }}
        
        QPushButton {{
            background-color: {cls.COLORS['button']};
            color: {cls.COLORS['text']};
            border: 1px solid {cls.COLORS['mid']};
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }}
        
        QPushButton:hover {{
            background-color: {cls.COLORS['light']};
            border-color: {cls.COLORS['highlight']};
        }}
        
        QPushButton:pressed {{
            background-color: {cls.COLORS['dark']};
        }}
        
        QLabel {{
            color: {cls.COLORS['text']};
            background-color: transparent;
        }}
        
        QListWidget {{
            background-color: {cls.COLORS['base']};
            color: {cls.COLORS['text']};
            border: 1px solid {cls.COLORS['mid']};
            border-radius: 4px;
            padding: 4px;
        }}
        
        QListWidget::item {{
            padding: 6px;
            border-radius: 2px;
            color: {cls.COLORS['text']};
        }}
        
        QListWidget::item:selected {{
            background-color: {cls.COLORS['highlight']};
            color: {cls.COLORS['highlighted_text']};
        }}
        
        QListWidget::item:hover {{
            background-color: {cls.COLORS['light']};
        }}
        
        QScrollBar:vertical {{
            background-color: {cls.COLORS['base']};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {cls.COLORS['mid']};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {cls.COLORS['light']};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QWidget {{
            background-color: {cls.COLORS['base']};
            color: {cls.COLORS['text']};
        }}
        
        QLineEdit {{
            background-color: {cls.COLORS['base']};
            color: {cls.COLORS['text']};
            border: 1px solid {cls.COLORS['mid']};
            border-radius: 4px;
            padding: 4px;
        }}
        
        QComboBox {{
            background-color: {cls.COLORS['base']};
            color: {cls.COLORS['text']};
            border: 1px solid {cls.COLORS['mid']};
            border-radius: 4px;
            padding: 4px;
        }}
        """

    @classmethod
    def _apply_matplotlib_theme(cls):
        """Apply dark theme to matplotlib charts."""
        # Set matplotlib style parameters
        rcParams["figure.facecolor"] = cls.COLORS["chart_background"]
        rcParams["axes.facecolor"] = cls.COLORS["chart_background"]
        rcParams["text.color"] = cls.COLORS["chart_text"]
        rcParams["axes.labelcolor"] = cls.COLORS["chart_text"]
        rcParams["xtick.color"] = cls.COLORS["chart_text"]
        rcParams["ytick.color"] = cls.COLORS["chart_text"]
        rcParams["axes.edgecolor"] = cls.COLORS["chart_grid"]
        rcParams["axes.grid"] = True
        rcParams["grid.color"] = cls.COLORS["chart_grid"]
        rcParams["grid.alpha"] = 0.3

    @classmethod
    def get_chart_colors(cls) -> dict:
        """Get chart colors for dark theme."""
        return {
            "background": cls.COLORS["chart_background"],
            "text": cls.COLORS["chart_text"],
            "grid": cls.COLORS["chart_grid"],
            "primary": cls.COLORS["chart_primary"],
            "secondary": cls.COLORS["chart_secondary"],
            "success": cls.COLORS["chart_success"],
            "warning": cls.COLORS["chart_warning"],
            "error": cls.COLORS["chart_error"],
        }
