"""
Chart widget for data visualization in the Cando application.

This module provides matplotlib-based chart widgets that can be embedded
in PySide6 interfaces for productivity analytics.
"""

from typing import Dict, List
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import QWidget, QVBoxLayout


class ChartWidget(QWidget):
    """
    Base chart widget that embeds matplotlib in PySide6.

    Provides a foundation for various chart types used in the dashboard.
    """

    def __init__(self, parent=None):
        """Initialize the chart widget with matplotlib figure."""
        super().__init__(parent)
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.axes = self.figure.add_subplot(111)

        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def clear(self):
        """Clear the current chart."""
        self.axes.clear()

    def update_chart(self):
        """Update the chart display."""
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
            )
            self.update_chart()
            return

        projects = list(project_times.keys())
        hours = list(project_times.values())

        bars = self.axes.bar(projects, hours, color="skyblue", alpha=0.7)
        self.axes.set_title("Time Spent by Project")
        self.axes.set_xlabel("Projects")
        self.axes.set_ylabel("Hours")
        self.axes.tick_params(axis="x", rotation=45)

        # Add value labels on bars
        for bar, hour in zip(bars, hours):
            height = bar.get_height()
            self.axes.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{hour:.1f}h",
                ha="center",
                va="bottom",
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
            )
            self.update_chart()
            return

        dates = list(daily_hours.keys())
        hours = list(daily_hours.values())

        self.axes.plot(dates, hours, marker="o", linewidth=2, markersize=6)
        self.axes.set_title("Daily Productivity")
        self.axes.set_xlabel("Date")
        self.axes.set_ylabel("Hours Worked")
        self.axes.tick_params(axis="x", rotation=45)
        self.axes.grid(True, alpha=0.3)

        # Add value labels on points
        for date, hour in zip(dates, hours):
            self.axes.annotate(
                f"{hour:.1f}h",
                (date, hour),
                textcoords="offset points",
                xytext=(0, 10),
                ha="center",
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
            )
            self.update_chart()
            return

        types = list(type_stats.keys())
        counts = list(type_stats.values())
        colors = ["lightcoral", "lightblue", "lightgreen", "gold", "lightpink"]

        wedges, texts, autotexts = self.axes.pie(
            counts, labels=types, autopct="%1.1f%%", colors=colors
        )
        self.axes.set_title("Timer Type Usage")

        self.figure.tight_layout()
        self.update_chart()
