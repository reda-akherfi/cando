"""
Chart widget for data visualization in the Cando application.

This module provides matplotlib-based chart widgets that can be embedded
in PySide6 interfaces for productivity analytics.
"""

from typing import Dict, List
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
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

        # Create figure with current theme and proper sizing
        self.figure = Figure(
            figsize=(8, 6), facecolor=self.colors["background"], dpi=100
        )
        self.canvas = FigureCanvas(self.figure)

        # Add navigation toolbar for interactive features
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Style the toolbar to match the theme
        self.toolbar.setStyleSheet(
            """
            QToolBar {
                background-color: #2d2d30;
                border: none;
                spacing: 2px;
                padding: 2px;
            }
            QToolButton {
                background-color: #3c3c3c;
                border: 1px solid #4c4c4c;
                border-radius: 3px;
                padding: 4px;
                color: #cccccc;
            }
            QToolButton:hover {
                background-color: #4c4c4c;
                border-color: #0078d4;
            }
            QToolButton:pressed {
                background-color: #0078d4;
            }
        """
        )

        # Create axes
        self.axes = self.figure.add_subplot(111, facecolor=self.colors["background"])

        # Apply current theme to the axes
        self.axes.set_facecolor(self.colors["background"])

        layout = QVBoxLayout(self)
        layout.addWidget(self.toolbar)
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
        # Ensure proper sizing
        self.figure.tight_layout()
        self.canvas.draw()

    def update_theme_colors(self):
        """Update the chart colors to match the current theme."""
        self.colors = self._get_current_theme_colors()
        self.figure.set_facecolor(self.colors["background"])
        self.axes.set_facecolor(self.colors["background"])
        self.canvas.draw()

    def resizeEvent(self, event):
        """Handle resize events to ensure charts fit properly."""
        super().resizeEvent(event)
        # Update the chart when the widget is resized
        if hasattr(self, "figure"):
            # Dynamically adjust figure size based on widget size
            widget_size = self.size()
            width_inches = widget_size.width() / 100.0
            height_inches = widget_size.height() / 100.0

            # Set minimum and maximum sizes
            width_inches = max(4, min(width_inches, 12))
            height_inches = max(3, min(height_inches, 8))

            self.figure.set_size_inches(width_inches, height_inches)
            self.figure.tight_layout()
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

        # Add value labels on bars with tooltips
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

        (line,) = self.axes.plot(
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

        self.update_chart()


class CumulativeWorkChart(ChartWidget):
    """Chart widget for displaying cumulative work hours over time."""

    def plot_cumulative_work(self, cumulative_data: Dict[str, float]):
        """
        Plot cumulative work hours as a line chart.

        Args:
            cumulative_data: Dictionary mapping dates to cumulative hours
        """
        self.clear()

        if not cumulative_data:
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

        dates = list(cumulative_data.keys())
        hours = list(cumulative_data.values())

        # Plot cumulative line
        (line,) = self.axes.plot(
            dates,
            hours,
            marker="o",
            linewidth=2,
            markersize=4,
            color=self.colors["primary"],
            label="Cumulative Hours",
        )

        # Fill area under the curve
        self.axes.fill_between(dates, hours, alpha=0.3, color=self.colors["primary"])

        self.axes.set_title(
            "Cumulative Work Hours",
            color=self.colors["text"],
            fontsize=14,
            fontweight="bold",
        )
        self.axes.set_xlabel("Date", color=self.colors["text"], fontsize=12)
        self.axes.set_ylabel("Cumulative Hours", color=self.colors["text"], fontsize=12)
        self.axes.tick_params(axis="x", rotation=45, colors=self.colors["text"])
        self.axes.tick_params(axis="y", colors=self.colors["text"])
        self.axes.grid(True, alpha=0.3, color=self.colors["grid"])

        # Add legend
        self.axes.legend(loc="upper left", framealpha=0.8)

        # Add value labels on key points (every 5th point to avoid clutter)
        for i, (date, hour) in enumerate(zip(dates, hours)):
            if (
                i % 5 == 0 or i == len(dates) - 1
            ):  # Show every 5th point and the last point
                self.axes.annotate(
                    f"{hour:.1f}h",
                    (date, hour),
                    textcoords="offset points",
                    xytext=(0, 10),
                    ha="center",
                    color=self.colors["text"],
                    fontweight="bold",
                    fontsize=8,
                )

        self.update_chart()


class TagDistributionChart(ChartWidget):
    """Chart widget for displaying tag distribution."""

    def plot_tag_distribution(self, tag_data: Dict[str, float]):
        """
        Plot tag distribution as a pie chart.

        Args:
            tag_data: Dictionary mapping tag names to hours worked
        """
        self.clear()

        if not tag_data:
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

        # Sort by hours to show most important tags first
        sorted_data = sorted(tag_data.items(), key=lambda x: x[1], reverse=True)
        tags = [item[0] for item in sorted_data]
        hours = [item[1] for item in sorted_data]

        # Use a color palette
        colors = plt.cm.Set3(range(len(tags)))

        wedges, texts, autotexts = self.axes.pie(
            hours, labels=tags, autopct="%1.1f%%", colors=colors
        )
        self.axes.set_title(
            "Time Distribution by Tags",
            color=self.colors["text"],
            fontsize=14,
            fontweight="bold",
        )

        # Style the text elements
        for text in texts:
            text.set_color(self.colors["text"])
            text.set_fontsize(9)

        for autotext in autotexts:
            autotext.set_color(self.colors["text"])
            autotext.set_fontweight("bold")
            autotext.set_fontsize(8)

        self.update_chart()


class ProjectDistributionChart(ChartWidget):
    """Chart widget for displaying project distribution."""

    def plot_project_distribution(self, project_data: Dict[str, float]):
        """
        Plot project distribution as a pie chart.

        Args:
            project_data: Dictionary mapping project names to hours worked
        """
        self.clear()

        if not project_data:
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

        # Sort by hours to show most important projects first
        sorted_data = sorted(project_data.items(), key=lambda x: x[1], reverse=True)
        projects = [item[0] for item in sorted_data]
        hours = [item[1] for item in sorted_data]

        # Use a color palette
        colors = plt.cm.Pastel1(range(len(projects)))

        wedges, texts, autotexts = self.axes.pie(
            hours, labels=projects, autopct="%1.1f%%", colors=colors
        )
        self.axes.set_title(
            "Time Distribution by Projects",
            color=self.colors["text"],
            fontsize=14,
            fontweight="bold",
        )

        # Style the text elements
        for text in texts:
            text.set_color(self.colors["text"])
            text.set_fontsize(9)

        for autotext in autotexts:
            autotext.set_color(self.colors["text"])
            autotext.set_fontweight("bold")
            autotext.set_fontsize(8)

        self.update_chart()
