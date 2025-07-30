"""
Chart widget for data visualization in the Cando application.

This module provides matplotlib-based chart widgets that can be embedded
in PySide6 interfaces for productivity analytics.
"""

from typing import Dict, List
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import QWidget, QVBoxLayout, QApplication
from PySide6.QtGui import QPalette
from app.ui.theme import DarkTheme, LightTheme


class ChartWidget(QWidget):
    """
    Base chart widget that embeds matplotlib in PySide6.

    Provides a foundation for various chart types used in the dashboard.
    """

    def __init__(self, parent=None):
        """Initialize the chart widget with matplotlib figure."""
        super().__init__(parent)
        self.colors = self._get_current_theme_colors()

        # Create figure with current theme
        self.figure = Figure(figsize=(8, 6), facecolor=self.colors["background"])
        self.canvas = FigureCanvas(self.figure)
        self.axes = self.figure.add_subplot(111, facecolor=self.colors["background"])

        # Apply current theme to the axes
        self.axes.set_facecolor(self.colors["background"])

        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def _get_current_theme_colors(self):
        """Get chart colors based on the current application theme."""
        app = QApplication.instance()
        if app:
            # Check if the application is using dark theme by looking at the palette
            palette = app.palette()
            window_color = palette.color(QPalette.ColorRole.Window)
            # If window color is dark, use dark theme colors
            if window_color.lightness() < 128:
                return DarkTheme.get_chart_colors()
            else:
                return LightTheme.get_chart_colors()
        # Default to dark theme if we can't determine
        return DarkTheme.get_chart_colors()

    def clear(self):
        """Clear the current chart."""
        self.axes.clear()
        # Update colors to current theme
        self.colors = self._get_current_theme_colors()
        self.axes.set_facecolor(self.colors["background"])
        self.figure.set_facecolor(self.colors["background"])

    def update_chart(self):
        """Update the chart display."""
        self.canvas.draw()

    def update_theme_colors(self):
        """Update the chart colors to match the current theme."""
        self.colors = self._get_current_theme_colors()
        self.figure.set_facecolor(self.colors["background"])
        self.axes.set_facecolor(self.colors["background"])
        self.canvas.draw()


class TimeByProjectChart(ChartWidget):
    """Chart widget for displaying time spent by project."""

    def plot_time_by_project(self, project_times: Dict[str, float]):
        """
        Plot time spent by project as a bar chart.

        Args:
            project_times: Dictionary mapping project names to hours spent
        """
        self.clear()

        if not project_times:
            self.axes.text(
                0.5,
                0.5,
                "No data available",
                ha="center",
                va="center",
                transform=self.axes.transAxes,
                color=self.colors["text"],
                fontsize=12,
            )
            self.update_chart()
            return

        projects = list(project_times.keys())
        hours = list(project_times.values())

        bars = self.axes.bar(projects, hours, color=self.colors["primary"], alpha=0.7)
        self.axes.set_title(
            "Time Spent by Project",
            color=self.colors["text"],
            fontsize=14,
            fontweight="bold",
        )
        self.axes.set_xlabel("Projects", color=self.colors["text"], fontsize=12)
        self.axes.set_ylabel("Hours", color=self.colors["text"], fontsize=12)
        self.axes.tick_params(axis="x", rotation=45, colors=self.colors["text"])
        self.axes.tick_params(axis="y", colors=self.colors["text"])

        # Set grid
        self.axes.grid(True, alpha=0.3, color=self.colors["grid"])

        # Add value labels on bars
        for bar, hour in zip(bars, hours):
            height = bar.get_height()
            self.axes.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{hour:.1f}h",
                ha="center",
                va="bottom",
                color=self.colors["text"],
                fontweight="bold",
            )

        self.figure.tight_layout()
        self.update_chart()


class DailyProductivityChart(ChartWidget):
    """Chart widget for displaying daily productivity trends."""

    def plot_daily_productivity(self, daily_hours: Dict[str, float]):
        """
        Plot daily productivity as a line chart.

        Args:
            daily_hours: Dictionary mapping dates to hours worked
        """
        self.clear()

        if not daily_hours:
            self.axes.text(
                0.5,
                0.5,
                "No data available",
                ha="center",
                va="center",
                transform=self.axes.transAxes,
                color=self.colors["text"],
                fontsize=12,
            )
            self.update_chart()
            return

        dates = list(daily_hours.keys())
        hours = list(daily_hours.values())

        self.axes.plot(
            dates,
            hours,
            marker="o",
            linewidth=2,
            markersize=6,
            color=self.colors["primary"],
        )
        self.axes.set_title(
            "Daily Productivity",
            color=self.colors["text"],
            fontsize=14,
            fontweight="bold",
        )
        self.axes.set_xlabel("Date", color=self.colors["text"], fontsize=12)
        self.axes.set_ylabel("Hours Worked", color=self.colors["text"], fontsize=12)
        self.axes.tick_params(axis="x", rotation=45, colors=self.colors["text"])
        self.axes.tick_params(axis="y", colors=self.colors["text"])
        self.axes.grid(True, alpha=0.3, color=self.colors["grid"])

        # Add value labels on points
        for date, hour in zip(dates, hours):
            self.axes.annotate(
                f"{hour:.1f}h",
                (date, hour),
                textcoords="offset points",
                xytext=(0, 10),
                ha="center",
                color=self.colors["text"],
                fontweight="bold",
            )

        self.figure.tight_layout()
        self.update_chart()


class TimerTypeChart(ChartWidget):
    """Chart widget for displaying timer type usage statistics."""

    def plot_timer_types(self, type_stats: Dict[str, int]):
        """
        Plot timer type usage as a pie chart.

        Args:
            type_stats: Dictionary mapping timer types to usage count
        """
        self.clear()

        if not type_stats:
            self.axes.text(
                0.5,
                0.5,
                "No data available",
                ha="center",
                va="center",
                transform=self.axes.transAxes,
                color=self.colors["text"],
                fontsize=12,
            )
            self.update_chart()
            return

        types = list(type_stats.keys())
        counts = list(type_stats.values())
        colors = [
            self.colors["primary"],
            self.colors["secondary"],
            self.colors["success"],
            self.colors["warning"],
            self.colors["error"],
        ]

        wedges, texts, autotexts = self.axes.pie(
            counts, labels=types, autopct="%1.1f%%", colors=colors
        )
        self.axes.set_title(
            "Timer Type Usage",
            color=self.colors["text"],
            fontsize=14,
            fontweight="bold",
        )

        # Style the text elements
        for text in texts:
            text.set_color(self.colors["text"])
            text.set_fontsize(10)

        for autotext in autotexts:
            autotext.set_color(self.colors["text"])
            autotext.set_fontweight("bold")

        self.figure.tight_layout()
        self.update_chart()
