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
    QCheckBox,
    QRadioButton,
    QButtonGroup,
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
    project_selected = Signal(int)  # Emits project_id
    task_selected = Signal(Task)  # Emits selected task

    def __init__(
        self,
        timer_controller: TimerController,
        db_service: DatabaseService,
        notification_manager=None,
        parent=None,
    ):
        super().__init__(parent)
        self.timer_controller = timer_controller
        self.db_service = db_service
        self.notification_manager = notification_manager
        self.current_task: Optional[Task] = None
        self.current_project_id: Optional[int] = None
        self._sync_in_progress = False  # Flag to prevent recursive synchronization
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # Update every second

        # Pomodoro settings
        self.work_duration = 25  # minutes
        self.short_break_duration = 5  # minutes
        self.long_break_duration = 15  # minutes
        self.autostart_breaks = True
        self.autostart_work = True

        self.setup_ui()
        self.refresh_projects()
        self.update_display()
        self.update_start_button_state()  # Set initial button state

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
        mode_layout = QHBoxLayout(mode_group)

        # Create radio buttons for timer modes
        self.mode_button_group = QButtonGroup()

        self.stopwatch_radio = QRadioButton("Stopwatch")
        self.stopwatch_radio.setChecked(True)  # Default selection
        self.mode_button_group.addButton(self.stopwatch_radio)
        mode_layout.addWidget(self.stopwatch_radio)

        self.countdown_radio = QRadioButton("Countdown")
        self.mode_button_group.addButton(self.countdown_radio)
        mode_layout.addWidget(self.countdown_radio)

        self.pomodoro_radio = QRadioButton("Pomodoro")
        self.mode_button_group.addButton(self.pomodoro_radio)
        mode_layout.addWidget(self.pomodoro_radio)

        # Connect the button group to the mode change handler
        self.mode_button_group.buttonClicked.connect(self.on_mode_changed)

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

        # Pomodoro settings
        self.pomodoro_group = QGroupBox("Pomodoro Settings")
        pomodoro_layout = QGridLayout(self.pomodoro_group)

        # Work duration
        pomodoro_layout.addWidget(QLabel("Work Duration (min):"), 0, 0)
        self.work_duration_spin = QSpinBox()
        self.work_duration_spin.setRange(1, 120)
        self.work_duration_spin.setValue(self.work_duration)
        self.work_duration_spin.valueChanged.connect(self.on_work_duration_changed)
        pomodoro_layout.addWidget(self.work_duration_spin, 0, 1)

        # Short break duration
        pomodoro_layout.addWidget(QLabel("Short Break (min):"), 1, 0)
        self.short_break_spin = QSpinBox()
        self.short_break_spin.setRange(1, 30)
        self.short_break_spin.setValue(self.short_break_duration)
        self.short_break_spin.valueChanged.connect(self.on_short_break_changed)
        pomodoro_layout.addWidget(self.short_break_spin, 1, 1)

        # Long break duration
        pomodoro_layout.addWidget(QLabel("Long Break (min):"), 2, 0)
        self.long_break_spin = QSpinBox()
        self.long_break_spin.setRange(5, 60)
        self.long_break_spin.setValue(self.long_break_duration)
        self.long_break_spin.valueChanged.connect(self.on_long_break_changed)
        pomodoro_layout.addWidget(self.long_break_spin, 2, 1)

        # Autostart options
        pomodoro_layout.addWidget(QLabel("Autostart Options:"), 3, 0)
        autostart_layout = QVBoxLayout()

        self.autostart_breaks_checkbox = QCheckBox("Auto-start breaks")
        self.autostart_breaks_checkbox.setChecked(self.autostart_breaks)
        self.autostart_breaks_checkbox.toggled.connect(self.on_autostart_breaks_changed)
        autostart_layout.addWidget(self.autostart_breaks_checkbox)

        self.autostart_work_checkbox = QCheckBox("Auto-start work sessions")
        self.autostart_work_checkbox.setChecked(self.autostart_work)
        self.autostart_work_checkbox.toggled.connect(self.on_autostart_work_changed)
        autostart_layout.addWidget(self.autostart_work_checkbox)

        pomodoro_layout.addLayout(autostart_layout, 3, 1)

        layout.addWidget(self.pomodoro_group)
        self.pomodoro_group.setVisible(False)

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
        if self._sync_in_progress:
            return

        self._sync_in_progress = True
        if index > 0:
            self.current_project_id = self.project_combo.itemData(index)
            self.task_combo.setEnabled(True)
            self.refresh_tasks(self.current_project_id)
            # Emit signal for synchronization
            self.project_selected.emit(self.current_project_id)
        else:
            self.current_project_id = None
            self.current_task = None
            self.task_combo.setEnabled(False)
            self.task_combo.clear()
            self.task_combo.addItem("Select a task...", None)
            # Emit signal for synchronization
            self.project_selected.emit(None)

        # Update start button state
        self.update_start_button_state()
        self._sync_in_progress = False

    def on_task_selected(self, index: int):
        """Handle task selection."""
        if self._sync_in_progress:
            return

        self._sync_in_progress = True
        if index > 0:
            self.current_task = self.task_combo.itemData(index)
            # Emit signal for synchronization
            self.task_selected.emit(self.current_task)
        else:
            self.current_task = None
            # Emit signal for synchronization
            self.task_selected.emit(None)

        # Update start button state
        self.update_start_button_state()
        self._sync_in_progress = False

    def on_mode_changed(self, button):
        """Handle timer mode changes."""
        mode = button.text().lower()
        self.countdown_group.setVisible(mode == "countdown")
        self.pomodoro_group.setVisible(mode == "pomodoro")
        self.progress_bar.setVisible(mode in ["countdown", "pomodoro"])

        if mode == "pomodoro":
            # Set default Pomodoro duration
            self.minutes_spin.setValue(self.work_duration)
            self.seconds_spin.setValue(0)
        elif mode == "countdown":
            self.minutes_spin.setValue(30)
            self.seconds_spin.setValue(0)

    def on_work_duration_changed(self, value: int):
        """Handle work duration change."""
        self.work_duration = value
        if self.get_current_mode() == "pomodoro":
            self.minutes_spin.setValue(value)

    def on_short_break_changed(self, value: int):
        """Handle short break duration change."""
        self.short_break_duration = value

    def on_long_break_changed(self, value: int):
        """Handle long break duration change."""
        self.long_break_duration = value

    def on_autostart_breaks_changed(self, checked: bool):
        """Handle autostart breaks setting change."""
        self.autostart_breaks = checked

    def on_autostart_work_changed(self, checked: bool):
        """Handle autostart work setting change."""
        self.autostart_work = checked

    def get_current_mode(self):
        """Get the currently selected timer mode from radio buttons."""
        if self.stopwatch_radio.isChecked():
            return "stopwatch"
        elif self.countdown_radio.isChecked():
            return "countdown"
        elif self.pomodoro_radio.isChecked():
            return "pomodoro"
        else:
            return "stopwatch"  # Default fallback

    def update_start_button_state(self):
        """Update the start button enabled state based on current selection."""
        can_start = self.current_task is not None
        self.start_button.setEnabled(can_start)

        # Update button text and styling based on state
        if can_start:
            self.start_button.setText("Start")
            self.start_button.setStyleSheet("")
        else:
            # Provide more specific guidance based on what's missing
            if self.current_project_id is None:
                self.start_button.setText("Select Project")
            else:
                self.start_button.setText("Select Task")
            self.start_button.setStyleSheet("color: #888;")

    def start_timer(self):
        """Start the timer."""
        if not self.current_task:
            if self.notification_manager:
                self.notification_manager.show_error(
                    "No Task Selected", "Please select a task first."
                )
            else:
                QMessageBox.warning(
                    self, "No Task Selected", "Please select a task first."
                )
            return

        mode = self.get_current_mode()

        if mode == "pomodoro":
            # Start a Pomodoro work session
            timer = self.timer_controller.start_pomodoro_session(
                self.current_task.id,
                "work",
                work_duration=self.work_duration,
                short_break_duration=self.short_break_duration,
                long_break_duration=self.long_break_duration,
            )
        elif mode == "countdown":
            duration = self.minutes_spin.value() * 60 + self.seconds_spin.value()
            if duration <= 0:
                if self.notification_manager:
                    self.notification_manager.show_error(
                        "Invalid Duration", "Please set a valid duration."
                    )
                else:
                    QMessageBox.warning(
                        self, "Invalid Duration", "Please set a valid duration."
                    )
                return
            timer = self.timer_controller.start_timer(
                self.current_task.id, mode, duration=duration
            )
        else:  # stopwatch
            timer = self.timer_controller.start_timer(self.current_task.id, mode)

        if timer:
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)

            if mode == "pomodoro":
                self.status_label.setText(f"Work Session: {self.current_task.name}")
            else:
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
            mode = self.get_current_mode()

            if mode == "pomodoro" and active_timer.duration:
                # Pomodoro countdown mode
                elapsed = datetime.now() - active_timer.start
                remaining = active_timer.duration - elapsed.total_seconds()

                if remaining <= 0:
                    # Timer completed
                    self.stop_timer()
                    self.timer_completed.emit(active_timer)

                    # Handle Pomodoro session completion
                    self.handle_pomodoro_completion(active_timer)
                    return

                # Display remaining time
                hours, remainder = divmod(remaining, 3600)
                minutes, seconds = divmod(remainder, 60)
                self.time_label.setText(
                    f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
                )

                # Update progress bar
                progress = (
                    (active_timer.duration - remaining) / active_timer.duration
                ) * 100
                self.progress_bar.setValue(int(progress))

                # Update status
                session_type = active_timer.pomodoro_session_type
                if session_type == "work":
                    self.status_label.setText(f"Work Session: {self.current_task.name}")
                elif session_type == "short_break":
                    self.status_label.setText("Short Break")
                elif session_type == "long_break":
                    self.status_label.setText("Long Break")

            else:
                # Stopwatch or countdown mode
                elapsed = datetime.now() - active_timer.start
                hours, remainder = divmod(elapsed.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)

                self.time_label.setText(
                    f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
                )

                if mode == "countdown" and active_timer.duration:
                    if active_timer.duration > 0:
                        progress = min(
                            100, (elapsed.total_seconds() / active_timer.duration) * 100
                        )
                        self.progress_bar.setValue(int(progress))

                        if elapsed.total_seconds() >= active_timer.duration:
                            self.stop_timer()
                            self.timer_completed.emit(active_timer)
                            if self.notification_manager:
                                self.notification_manager.show_success(
                                    "Timer Complete", "Your timer has finished!"
                                )
                            else:
                                QMessageBox.information(
                                    self, "Timer Complete", "Your timer has finished!"
                                )
        else:
            self.time_label.setText("00:00:00")
            self.progress_bar.setValue(0)

    def handle_pomodoro_completion(self, completed_timer: Timer):
        """Handle Pomodoro session completion and autostart logic."""
        session_type = completed_timer.pomodoro_session_type

        if session_type == "work":
            # Work session completed
            if self.notification_manager:
                self.notification_manager.show_success(
                    "Work Session Complete!",
                    f"Great job! You've completed work session #{completed_timer.pomodoro_session_number}. Time for a break!",
                )
            else:
                QMessageBox.information(
                    self,
                    "Work Session Complete!",
                    f"Great job! You've completed work session #{completed_timer.pomodoro_session_number}.\n\n"
                    "Time for a break!",
                )

            if self.autostart_breaks:
                # Auto-start break
                next_session_type = (
                    self.timer_controller.get_next_pomodoro_session_type()
                )
                if next_session_type == "short_break":
                    self.start_break_session("short_break")
                else:
                    self.start_break_session("long_break")

        elif session_type in ["short_break", "long_break"]:
            # Break completed
            break_type = "Short" if session_type == "short_break" else "Long"
            if self.notification_manager:
                self.notification_manager.show_success(
                    f"{break_type} Break Complete!",
                    "Break time is over. Ready to get back to work?",
                )
            else:
                QMessageBox.information(
                    self,
                    f"{break_type} Break Complete!",
                    f"Break time is over. Ready to get back to work?",
                )

            if self.autostart_work:
                # Auto-start next work session
                self.start_work_session()

    def start_work_session(self):
        """Start a new Pomodoro work session."""
        if not self.current_task:
            if self.notification_manager:
                self.notification_manager.show_error(
                    "No Task Selected", "Please select a task first."
                )
            else:
                QMessageBox.warning(
                    self, "No Task Selected", "Please select a task first."
                )
            return

        timer = self.timer_controller.start_pomodoro_session(
            self.current_task.id,
            "work",
            work_duration=self.work_duration,
            short_break_duration=self.short_break_duration,
            long_break_duration=self.long_break_duration,
        )
        if timer:
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_label.setText(f"Work Session: {self.current_task.name}")
            self.timer_started.emit(timer)

    def start_break_session(self, break_type: str):
        """Start a Pomodoro break session."""
        if not self.current_task:
            if self.notification_manager:
                self.notification_manager.show_error(
                    "No Task Selected", "Please select a task first."
                )
            else:
                QMessageBox.warning(
                    self, "No Task Selected", "Please select a task first."
                )
            return

        timer = self.timer_controller.start_pomodoro_session(
            self.current_task.id,
            break_type,
            work_duration=self.work_duration,
            short_break_duration=self.short_break_duration,
            long_break_duration=self.long_break_duration,
        )
        if timer:
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            break_label = "Short Break" if break_type == "short_break" else "Long Break"
            self.status_label.setText(break_label)
            self.timer_started.emit(timer)

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

                    # Format timer information
                    time_str = f"{timer.start.strftime('%H:%M')} - {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

                    if timer.type == "pomodoro" and timer.pomodoro_session_type:
                        session_info = (
                            f" ({timer.pomodoro_session_type.replace('_', ' ').title()}"
                        )
                        if timer.pomodoro_session_number:
                            session_info += f" #{timer.pomodoro_session_number}"
                        session_info += ")"
                        item_text = f"{time_str}{session_info}"
                    else:
                        item_text = f"{time_str} ({timer.type})"

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

        # Update Pomodoro statistics if we have a current task
        if self.current_task:
            pomodoro_stats = self.timer_controller.get_pomodoro_stats(
                self.current_task.id
            )
            # You could add more Pomodoro-specific UI elements here to display these stats

    def set_current_task(self, task: Task):
        """Set the current task externally."""
        self._sync_in_progress = True
        self.current_task = task
        for i in range(self.task_combo.count()):
            combo_task = self.task_combo.itemData(i)
            if (
                combo_task and combo_task.id == task.id
            ):  # Compare by ID instead of object reference
                self.task_combo.setCurrentIndex(i)
                break
        self._sync_in_progress = False
        self.update_start_button_state()

    def set_current_project(self, project_id: int):
        """Set the current project externally."""
        self._sync_in_progress = True
        # Find the project in the combo box and select it
        for i in range(self.project_combo.count()):
            if self.project_combo.itemData(i) == project_id:
                self.project_combo.setCurrentIndex(i)
                # Update internal state without triggering signals
                self.current_project_id = project_id
                self.task_combo.setEnabled(True)
                self.refresh_tasks(project_id)
                break
        self._sync_in_progress = False
        self.update_start_button_state()

    def set_current_project_and_task(self, project_id: int, task: Task):
        """Set both project and task externally."""
        self._sync_in_progress = True
        # First set the project
        self.set_current_project(project_id)
        # Refresh tasks for the project
        self.refresh_tasks(project_id)
        # Then set the task
        if task:
            self.set_current_task(task)
        self._sync_in_progress = False
        self.update_start_button_state()
