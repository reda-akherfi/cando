"""
Timer widget for the Cando application.
"""

from datetime import datetime, timedelta
from typing import Optional
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QGroupBox,
    QGridLayout,
    QSpinBox,
    QMessageBox,
)
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QFont
from app.models.timer import Timer
from app.models.task import Task
from app.controllers.timer_controller import TimerController
from app.services.database import DatabaseService


class TimerWidget(QWidget):
    """Comprehensive timer widget with multiple modes and task integration."""

    timer_started = Signal(Timer)
    timer_stopped = Signal(Timer)
    timer_completed = Signal(Timer)

    def __init__(
        self,
        timer_controller: TimerController,
        db_service: DatabaseService,
        parent=None,
    ):
        super().__init__(parent)
        self.timer_controller = timer_controller
        self.db_service = db_service
        self.current_task: Optional[Task] = None
        self.current_project_id: Optional[int] = None
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # Update every second

        self.setup_ui()
        self.refresh_projects()
        self.update_display()

    def setup_ui(self):
        """Set up the timer user interface."""
        layout = QVBoxLayout(self)

        # Project and Task selection
        selection_group = QGroupBox("Select Project & Task")
        selection_layout = QHBoxLayout(selection_group)

        # Project selection
        project_layout = QVBoxLayout()
        project_layout.addWidget(QLabel("Project:"))
        self.project_combo = QComboBox()
        self.project_combo.currentIndexChanged.connect(self.on_project_selected)
        project_layout.addWidget(self.project_combo)
        selection_layout.addLayout(project_layout)

        # Task selection
        task_layout = QVBoxLayout()
        task_layout.addWidget(QLabel("Task:"))
        self.task_combo = QComboBox()
        self.task_combo.currentIndexChanged.connect(self.on_task_selected)
        self.task_combo.setEnabled(False)  # Disabled until project is selected
        task_layout.addWidget(self.task_combo)
        selection_layout.addLayout(task_layout)

        layout.addWidget(selection_group)

        # Timer mode selection
        mode_group = QGroupBox("Timer Mode")
        mode_layout = QVBoxLayout(mode_group)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Stopwatch", "Countdown", "Pomodoro"])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        layout.addWidget(mode_group)

        # Countdown settings
        self.countdown_group = QGroupBox("Countdown Settings")
        countdown_layout = QGridLayout(self.countdown_group)
        countdown_layout.addWidget(QLabel("Minutes:"), 0, 0)
        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(1, 480)
        self.minutes_spin.setValue(25)
        countdown_layout.addWidget(self.minutes_spin, 0, 1)
        countdown_layout.addWidget(QLabel("Seconds:"), 1, 0)
        self.seconds_spin = QSpinBox()
        self.seconds_spin.setRange(0, 59)
        self.seconds_spin.setValue(0)
        countdown_layout.addWidget(self.seconds_spin, 1, 1)
        layout.addWidget(self.countdown_group)
        self.countdown_group.setVisible(False)

        # Timer display
        display_group = QGroupBox("Timer")
        display_layout = QVBoxLayout(display_group)
        self.time_label = QLabel("00:00:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setFont(QFont("Arial", 48, QFont.Bold))
        self.time_label.setStyleSheet("color: #4CAF50;")
        display_layout.addWidget(self.time_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        display_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready to start")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #888; font-size: 14px;")
        display_layout.addWidget(self.status_label)
        layout.addWidget(display_group)

        # Timer controls
        controls_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_timer)
        self.start_button.setMinimumHeight(40)
        controls_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_timer)
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setEnabled(False)
        controls_layout.addWidget(self.stop_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_timer)
        self.reset_button.setMinimumHeight(40)
        controls_layout.addWidget(self.reset_button)
        layout.addLayout(controls_layout)

        # Timer history
        history_group = QGroupBox("Recent Timers")
        history_layout = QVBoxLayout(history_group)
        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(150)
        history_layout.addWidget(self.history_list)
        layout.addWidget(history_group)

        # Statistics
        stats_group = QGroupBox("Today's Statistics")
        stats_layout = QGridLayout(stats_group)
        stats_layout.addWidget(QLabel("Total Time:"), 0, 0)
        self.total_time_label = QLabel("0h 0m")
        stats_layout.addWidget(self.total_time_label, 0, 1)
        stats_layout.addWidget(QLabel("Sessions:"), 1, 0)
        self.sessions_label = QLabel("0")
        stats_layout.addWidget(self.sessions_label, 1, 1)
        stats_layout.addWidget(QLabel("Average Session:"), 2, 0)
        self.avg_session_label = QLabel("0m")
        stats_layout.addWidget(self.avg_session_label, 2, 1)
        layout.addWidget(stats_group)

        layout.addStretch()

    def refresh_projects(self):
        """Refresh the project list in the combo box."""
        self.project_combo.clear()
        self.project_combo.addItem("Select a project...", None)
        projects = self.db_service.get_projects()
        for project in projects:
            self.project_combo.addItem(project.name, project.id)

    def refresh_tasks(self, project_id: Optional[int] = None):
        """Refresh the task list in the combo box for the selected project."""
        self.task_combo.clear()
        self.task_combo.addItem("Select a task...", None)

        if project_id is not None:
            tasks = self.db_service.get_tasks(project_id=project_id)
            for task in tasks:
                self.task_combo.addItem(task.name, task)

    def on_project_selected(self, index: int):
        """Handle project selection."""
        if index > 0:
            self.current_project_id = self.project_combo.itemData(index)
            self.task_combo.setEnabled(True)
            self.refresh_tasks(self.current_project_id)
        else:
            self.current_project_id = None
            self.current_task = None
            self.task_combo.setEnabled(False)
            self.task_combo.clear()
            self.task_combo.addItem("Select a task...", None)

    def on_task_selected(self, index: int):
        """Handle task selection."""
        if index > 0:
            self.current_task = self.task_combo.itemData(index)
        else:
            self.current_task = None

    def on_mode_changed(self, mode: str):
        """Handle timer mode changes."""
        self.countdown_group.setVisible(mode in ["Countdown", "Pomodoro"])
        self.progress_bar.setVisible(mode in ["Countdown", "Pomodoro"])
        if mode == "Pomodoro":
            self.minutes_spin.setValue(25)
            self.seconds_spin.setValue(0)
        elif mode == "Countdown":
            self.minutes_spin.setValue(30)
            self.seconds_spin.setValue(0)

    def start_timer(self):
        """Start the timer."""
        if not self.current_task:
            QMessageBox.warning(self, "No Task Selected", "Please select a task first.")
            return

        mode = self.mode_combo.currentText().lower()
        duration = None
        if mode in ["countdown", "pomodoro"]:
            duration = self.minutes_spin.value() * 60 + self.seconds_spin.value()
            if duration <= 0:
                QMessageBox.warning(
                    self, "Invalid Duration", "Please set a valid duration."
                )
                return

        timer = self.timer_controller.start_timer(self.current_task.id, mode)
        if timer:
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_label.setText(f"Running: {self.current_task.name}")
            self.timer_started.emit(timer)

    def stop_timer(self):
        """Stop the timer."""
        timer = self.timer_controller.stop_timer()
        if timer:
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_label.setText("Timer stopped")
            self.timer_stopped.emit(timer)
            self.refresh_history()
            self.update_statistics()

    def reset_timer(self):
        """Reset the timer display."""
        self.time_label.setText("00:00:00")
        self.progress_bar.setValue(0)
        self.status_label.setText("Ready to start")

    def update_display(self):
        """Update the timer display."""
        active_timer = self.timer_controller.get_active_timer()

        if active_timer:
            elapsed = datetime.now() - active_timer.start
            hours, remainder = divmod(elapsed.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)

            self.time_label.setText(
                f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            )

            mode = self.mode_combo.currentText().lower()
            if mode in ["countdown", "pomodoro"]:
                total_duration = (
                    self.minutes_spin.value() * 60 + self.seconds_spin.value()
                )
                if total_duration > 0:
                    progress = min(
                        100, (elapsed.total_seconds() / total_duration) * 100
                    )
                    self.progress_bar.setValue(int(progress))

                    if elapsed.total_seconds() >= total_duration:
                        self.stop_timer()
                        self.timer_completed.emit(active_timer)
                        QMessageBox.information(
                            self, "Timer Complete", "Your timer has finished!"
                        )
        else:
            self.time_label.setText("00:00:00")
            self.progress_bar.setValue(0)

    def refresh_history(self):
        """Refresh the timer history list."""
        self.history_list.clear()
        if self.current_task:
            timers = self.timer_controller.get_task_timers(self.current_task.id)
            for timer in timers[-10:]:
                if timer.end:
                    duration = timer.end - timer.start
                    hours, remainder = divmod(duration.total_seconds(), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    item_text = f"{timer.start.strftime('%H:%M')} - {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d} ({timer.type})"
                    item = QListWidgetItem(item_text)
                    self.history_list.addItem(item)

    def update_statistics(self):
        """Update the statistics display."""
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())

        all_timers = self.timer_controller.get_all_timers()
        today_timers = [
            t for t in all_timers if t.end and today_start <= t.end <= today_end
        ]

        total_seconds = sum((t.end - t.start).total_seconds() for t in today_timers)
        hours, remainder = divmod(total_seconds, 3600)
        minutes = remainder // 60

        self.total_time_label.setText(f"{int(hours)}h {int(minutes)}m")
        self.sessions_label.setText(str(len(today_timers)))

        if today_timers:
            avg_seconds = total_seconds / len(today_timers)
            avg_minutes = avg_seconds // 60
            self.avg_session_label.setText(f"{int(avg_minutes)}m")
        else:
            self.avg_session_label.setText("0m")

    def set_current_task(self, task: Task):
        """Set the current task externally."""
        self.current_task = task
        for i in range(self.task_combo.count()):
            if self.task_combo.itemData(i) == task:
                self.task_combo.setCurrentIndex(i)
                break
