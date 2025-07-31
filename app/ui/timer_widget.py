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
    QToolButton,
    QDialog,
)
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QFont, QIcon
from app.models.timer import Timer
from app.models.task import Task
from app.controllers.timer_controller import TimerController
from app.services.database import DatabaseService
from app.ui.countdown_settings_dialog import CountdownSettingsDialog
from app.ui.pomodoro_settings_dialog import PomodoroSettingsDialog


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

        # Countdown settings
        self.countdown_minutes = 30
        self.countdown_seconds = 0

        self.setup_ui()
        self.refresh_projects()
        self.update_display()
        self.update_start_button_state()  # Set initial button state

        # Print initial settings for debugging
        print("=== Initial Timer Widget Settings ===")
        self.print_current_settings()

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

        # Add spacer to push settings button to the right
        mode_layout.addStretch()

        # Settings button (cog wheel)
        self.settings_button = QToolButton()
        self.settings_button.setText("⚙")  # Unicode cog wheel as text
        self.settings_button.setToolTip("Timer Settings")
        self.settings_button.setEnabled(False)  # Disabled by default (stopwatch mode)
        self.settings_button.clicked.connect(self.open_settings_dialog)
        # Set a minimum size to ensure the button is visible
        self.settings_button.setMinimumSize(30, 30)
        # Style the button to make it look more like a settings button
        self.settings_button.setStyleSheet(
            """
            QToolButton {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f8f8f8;
                font-size: 14px;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: #e0e0e0;
            }
            QToolButton:disabled {
                background-color: #f0f0f0;
                color: #999;
            }
        """
        )
        mode_layout.addWidget(self.settings_button)

        # Connect the button group to the mode change handler
        self.mode_button_group.buttonClicked.connect(self.on_mode_changed)

        layout.addWidget(mode_group)

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

        # Enable/disable settings button based on mode
        self.settings_button.setEnabled(mode in ["countdown", "pomodoro"])

        # Show/hide progress bar based on mode
        self.progress_bar.setVisible(mode in ["countdown", "pomodoro"])

    def open_settings_dialog(self):
        """Open the appropriate settings dialog based on current mode."""
        mode = self.get_current_mode()

        if mode == "countdown":
            print(
                "Opening countdown dialog with values:",
                self.countdown_minutes,
                self.countdown_seconds,
            )
            dialog = CountdownSettingsDialog(
                minutes=self.countdown_minutes,
                seconds=self.countdown_seconds,
                parent=self,
            )
            if dialog.exec() == QDialog.Accepted:
                settings = dialog.get_settings()
                self.countdown_minutes = settings["minutes"]
                self.countdown_seconds = settings["seconds"]
                print(
                    "Countdown settings now:",
                    self.countdown_minutes,
                    self.countdown_seconds,
                )
                self.apply_settings_to_ui()
                self.print_current_settings()

        elif mode == "pomodoro":
            print(
                "Opening pomodoro dialog with values:",
                self.work_duration,
                self.short_break_duration,
                self.long_break_duration,
                self.autostart_breaks,
                self.autostart_work,
            )
            dialog = PomodoroSettingsDialog(
                work_duration=self.work_duration,
                short_break_duration=self.short_break_duration,
                long_break_duration=self.long_break_duration,
                autostart_breaks=self.autostart_breaks,
                autostart_work=self.autostart_work,
                parent=self,
            )
            if dialog.exec() == QDialog.Accepted:
                settings = dialog.get_settings()
                self.work_duration = settings["work_duration"]
                self.short_break_duration = settings["short_break_duration"]
                self.long_break_duration = settings["long_break_duration"]
                self.autostart_breaks = settings["autostart_breaks"]
                self.autostart_work = settings["autostart_work"]
                print(
                    "Pomodoro settings now:",
                    self.work_duration,
                    self.short_break_duration,
                    self.long_break_duration,
                    self.autostart_breaks,
                    self.autostart_work,
                )
                self.apply_settings_to_ui()
                self.print_current_settings()

    def apply_settings_to_ui(self):
        """Update any UI elements if needed after settings change."""
        # For now, nothing to update, but this is a placeholder for future UI sync.
        pass

    def print_current_settings(self):
        """Print current settings for debugging."""
        print("=== Current Settings ===")
        print(f"Countdown: {self.countdown_minutes}m {self.countdown_seconds}s")
        print(f"Pomodoro Work: {self.work_duration}m")
        print(f"Pomodoro Short Break: {self.short_break_duration}m")
        print(f"Pomodoro Long Break: {self.long_break_duration}m")
        print(f"Autostart Breaks: {self.autostart_breaks}")
        print(f"Autostart Work: {self.autostart_work}")
        print("=======================")

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
            print(
                "Starting pomodoro with values:",
                self.work_duration,
                self.short_break_duration,
                self.long_break_duration,
            )
            # Start a Pomodoro work session
            timer = self.timer_controller.start_pomodoro_session(
                self.current_task.id,
                "work",
                work_duration=self.work_duration,
                short_break_duration=self.short_break_duration,
                long_break_duration=self.long_break_duration,
            )
        elif mode == "countdown":
            print(
                "Starting countdown with values:",
                self.countdown_minutes,
                self.countdown_seconds,
            )
            duration = self.countdown_minutes * 60 + self.countdown_seconds
            print(f"Calculated countdown duration: {duration} seconds")
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
            print("Timer started successfully with mode:", mode)

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

        print(
            "Starting work session with values:",
            self.work_duration,
            self.short_break_duration,
            self.long_break_duration,
        )
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

        print(
            "Starting break session with values:",
            self.work_duration,
            self.short_break_duration,
            self.long_break_duration,
        )
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
