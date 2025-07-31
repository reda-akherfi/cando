"""
Timer history dialog for displaying recent timers.
"""

from datetime import datetime
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QScrollArea,
    QWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from app.models.timer import Timer
from app.services.database import DatabaseService


class TimerHistoryDialog(QDialog):
    """Dialog for displaying timer history in a table format."""

    def __init__(self, db_service: DatabaseService, parent=None):
        super().__init__(parent)
        self.db_service = db_service
        self.setup_ui()
        self.load_timer_history()

    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Timer History")
        self.setModal(True)
        self.setFixedSize(900, 600)

        # Center the dialog on the parent with better positioning
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2

            # Ensure the dialog doesn't go off-screen
            screen_geometry = self.screen().geometry()
            if x < screen_geometry.x():
                x = screen_geometry.x() + 20
            if y < screen_geometry.y():
                y = screen_geometry.y() + 20
            if x + self.width() > screen_geometry.x() + screen_geometry.width():
                x = screen_geometry.x() + screen_geometry.width() - self.width() - 20
            if y + self.height() > screen_geometry.y() + screen_geometry.height():
                y = screen_geometry.y() + screen_geometry.height() - self.height() - 20

            self.move(x, y)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Title
        title_label = QLabel("Recent Timer Sessions")
        title_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; margin-bottom: 10px;"
        )
        layout.addWidget(title_label)

        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "Project",
                "Task",
                "Type",
                "Start Time",
                "End Time",
                "Duration",
                "Session Info",
            ]
        )

        # Set table properties
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Project
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Task
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Type
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Start Time
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # End Time
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Duration
        header.setSectionResizeMode(6, QHeaderView.Stretch)  # Session Info

        # Set table style
        self.table.setStyleSheet(
            """
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
                alternate-background-color: #f8f8f8;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 8px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """
        )

        layout.addWidget(self.table)

        # Buttons (outside scroll area)
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setMinimumWidth(80)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)

    def load_timer_history(self):
        """Load and display the last 50 timers."""
        # Get all timers and sort by start time (most recent first)
        all_timers = self.db_service.get_timers()
        sorted_timers = sorted(all_timers, key=lambda t: t.start, reverse=True)

        # Take the last 50
        recent_timers = sorted_timers[:50]

        # Clear table
        self.table.setRowCount(len(recent_timers))

        for row, timer in enumerate(recent_timers):
            # Get project and task info
            task = self.db_service.get_task(timer.task_id)
            project = self.db_service.get_project(task.project_id) if task else None

            # Project name
            project_name = project.name if project else "Unknown Project"
            self.table.setItem(row, 0, QTableWidgetItem(project_name))

            # Task name
            task_name = task.name if task else "Unknown Task"
            self.table.setItem(row, 1, QTableWidgetItem(task_name))

            # Timer type
            timer_type = timer.type.title()
            self.table.setItem(row, 2, QTableWidgetItem(timer_type))

            # Start time
            start_time = timer.start.strftime("%Y-%m-%d %H:%M:%S")
            self.table.setItem(row, 3, QTableWidgetItem(start_time))

            # End time
            if timer.end:
                end_time = timer.end.strftime("%Y-%m-%d %H:%M:%S")
            else:
                end_time = "Running..."
            self.table.setItem(row, 4, QTableWidgetItem(end_time))

            # Duration
            if timer.end:
                if timer.duration is not None:
                    # Use stored effective duration (for timers with pauses)
                    duration_seconds = timer.duration
                else:
                    # Calculate raw duration (for timers without pauses)
                    duration = timer.end - timer.start
                    duration_seconds = duration.total_seconds()

                hours, remainder = divmod(duration_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                duration_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            else:
                duration_str = "Running..."
            self.table.setItem(row, 5, QTableWidgetItem(duration_str))

            # Session info (for Pomodoro)
            session_info = ""
            if timer.type == "pomodoro" and timer.pomodoro_session_type:
                session_type = timer.pomodoro_session_type.replace("_", " ").title()
                session_info = session_type
                if timer.pomodoro_session_number:
                    session_info += f" #{timer.pomodoro_session_number}"
            elif timer.type == "countdown" and timer.duration:
                target_duration = timer.duration
                target_hours, target_remainder = divmod(target_duration, 3600)
                target_minutes, target_seconds = divmod(target_remainder, 60)
                session_info = f"Target: {int(target_hours):02d}:{int(target_minutes):02d}:{int(target_seconds):02d}"

            self.table.setItem(row, 6, QTableWidgetItem(session_info))

            # Color code based on timer type
            if timer.type == "pomodoro":
                self.table.item(row, 2).setBackground(
                    QColor(211, 211, 211)
                )  # Light gray
            elif timer.type == "countdown":
                self.table.item(row, 2).setBackground(
                    QColor(173, 216, 230)
                )  # Light blue
            elif timer.type == "stopwatch":
                self.table.item(row, 2).setBackground(
                    QColor(144, 238, 144)
                )  # Light green
