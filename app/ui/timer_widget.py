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
from app.ui.timer_history_dialog import TimerHistoryDialog


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
        self.update_timer.start(100)  # Update every 100ms for smoother display

        # Track if we have an active timer to optimize updates
        self._has_active_timer = False

        # Load timer settings from database
        settings = self.db_service.load_timer_settings()

        # Pomodoro settings
        self.work_duration = settings["work_duration"]  # minutes
        self.short_break_duration = settings["short_break_duration"]  # minutes
        self.long_break_duration = settings["long_break_duration"]  # minutes
        self.autostart_breaks = settings["autostart_breaks"]
        self.autostart_work = settings["autostart_work"]
        self.work_count_down = settings["work_count_down"]
        self.short_break_count_down = settings["short_break_count_down"]
        self.long_break_count_down = settings["long_break_count_down"]

        # Countdown settings
        self.countdown_minutes = settings["countdown_minutes"]
        self.countdown_seconds = settings["countdown_seconds"]
        self.countdown_count_down = settings["countdown_count_down"]

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

        # History button
        self.view_history_button = QPushButton("History")
        self.view_history_button.setToolTip("View Timer History")
        self.view_history_button.clicked.connect(self.open_timer_history)
        self.view_history_button.setMinimumSize(60, 30)
        self.view_history_button.setStyleSheet(
            """
            QPushButton {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f8f8f8;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """
        )
        mode_layout.addWidget(self.view_history_button)

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

        # Add spacer to push buttons to the left
        mode_layout.addStretch()

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

        self.status_label = QLabel("Ready to start")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #888; font-size: 14px;")
        display_layout.addWidget(self.status_label)
        layout.addWidget(display_group)

        # Timer controls
        controls_layout = QHBoxLayout()

        # Start/Continue button
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_timer)
        self.start_button.setMinimumHeight(40)
        controls_layout.addWidget(self.start_button)

        # Pause button
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_timer)
        self.pause_button.setMinimumHeight(40)
        self.pause_button.setEnabled(False)
        controls_layout.addWidget(self.pause_button)

        # Finish button (for stopwatch/countdown)
        self.finish_button = QPushButton("Finish")
        self.finish_button.clicked.connect(self.finish_timer)
        self.finish_button.setMinimumHeight(40)
        self.finish_button.setEnabled(False)
        controls_layout.addWidget(self.finish_button)

        # Skip button (for pomodoro)
        self.skip_button = QPushButton("Skip")
        self.skip_button.clicked.connect(self.skip_timer)
        self.skip_button.setMinimumHeight(40)
        self.skip_button.setEnabled(False)
        controls_layout.addWidget(self.skip_button)

        # Reset button (for pomodoro)
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_timer)
        self.reset_button.setMinimumHeight(40)
        self.reset_button.setEnabled(False)
        controls_layout.addWidget(self.reset_button)

        layout.addLayout(controls_layout)

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

        # Initialize button states for the default mode (stopwatch)
        self._update_button_states_for_mode("stopwatch")

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
        mode = self.get_current_mode()
        print(f"Timer mode changed to: {mode}")

        # Enable/disable settings button based on mode
        self.settings_button.setEnabled(mode in ["countdown", "pomodoro"])

        # Update button states for the new mode
        self._update_button_states_for_mode(mode)

        # Update start button state
        self.update_start_button_state()

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
                count_down=self.countdown_count_down,
                parent=self,
            )
            if dialog.exec() == QDialog.Accepted:
                settings = dialog.get_settings()
                self.countdown_minutes = settings["minutes"]
                self.countdown_seconds = settings["seconds"]
                self.countdown_count_down = settings["count_down"]
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
                work_count_down=self.work_count_down,
                short_break_count_down=self.short_break_count_down,
                long_break_count_down=self.long_break_count_down,
                parent=self,
            )
            if dialog.exec() == QDialog.Accepted:
                settings = dialog.get_settings()
                self.work_duration = settings["work_duration"]
                self.short_break_duration = settings["short_break_duration"]
                self.long_break_duration = settings["long_break_duration"]
                self.autostart_breaks = settings["autostart_breaks"]
                self.autostart_work = settings["autostart_work"]
                self.work_count_down = settings["work_count_down"]
                self.short_break_count_down = settings["short_break_count_down"]
                self.long_break_count_down = settings["long_break_count_down"]
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
        # Save settings to database
        self.save_settings_to_database()

    def save_settings_to_database(self):
        """Save current timer settings to the database."""
        settings = {
            "countdown_minutes": self.countdown_minutes,
            "countdown_seconds": self.countdown_seconds,
            "countdown_count_down": self.countdown_count_down,
            "work_duration": self.work_duration,
            "short_break_duration": self.short_break_duration,
            "long_break_duration": self.long_break_duration,
            "autostart_breaks": self.autostart_breaks,
            "autostart_work": self.autostart_work,
            "work_count_down": self.work_count_down,
            "short_break_count_down": self.short_break_count_down,
            "long_break_count_down": self.long_break_count_down,
        }
        self.db_service.save_timer_settings(settings)

    def print_current_settings(self):
        """Print current settings for debugging."""
        print("=== Current Settings ===")
        print(
            f"Countdown: {self.countdown_minutes}m {self.countdown_seconds}s (count down: {self.countdown_count_down})"
        )
        print(
            f"Pomodoro Work: {self.work_duration}m (count down: {self.work_count_down})"
        )
        print(
            f"Pomodoro Short Break: {self.short_break_duration}m (count down: {self.short_break_count_down})"
        )
        print(
            f"Pomodoro Long Break: {self.long_break_duration}m (count down: {self.long_break_count_down})"
        )
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
        """Start or continue the timer."""
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
        timer = None

        # Check if we have a paused timer to resume
        if self.timer_controller.is_timer_paused():
            timer = self.timer_controller.resume_timer()
            if timer:
                self.start_button.setText("Continue")
                self.start_button.setEnabled(False)
                self.pause_button.setEnabled(True)
                self._update_button_states_for_mode(mode)
                self.timer_started.emit(timer)
                return
        else:
            # Start a new timer
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
                    work_count_down=self.work_count_down,
                    short_break_count_down=self.short_break_count_down,
                    long_break_count_down=self.long_break_count_down,
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
                    self.current_task.id,
                    mode,
                    duration=duration,
                    count_down=self.countdown_count_down,
                )
            else:  # stopwatch
                timer = self.timer_controller.start_timer(self.current_task.id, mode)

        if timer:
            self.start_button.setText("Continue")
            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self._update_button_states_for_mode(mode)

            if mode == "pomodoro":
                self.status_label.setText(f"Work Session: {self.current_task.name}")
            else:
                self.status_label.setText(f"Running: {self.current_task.name}")

            self.timer_started.emit(timer)
            print("Timer started successfully with mode:", mode)

    def pause_timer(self):
        """Pause the timer."""
        timer = self.timer_controller.pause_timer()
        if timer:
            self.start_button.setText("Continue")
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.status_label.setText("Timer paused")
            self.timer_stopped.emit(timer)

    def finish_timer(self):
        """Finish the timer (stop and reset display)."""
        timer = self.timer_controller.stop_timer()
        if timer:
            self.start_button.setText("Start")
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.finish_button.setEnabled(False)
            self.skip_button.setEnabled(False)
            self.reset_button.setEnabled(False)
            self.time_label.setText("00:00:00")
            self.status_label.setText("Ready to start")
            self.timer_stopped.emit(timer)
            self.update_statistics()

    def skip_timer(self):
        """Skip to the next Pomodoro session."""
        mode = self.get_current_mode()
        if mode == "pomodoro":
            timer = self.timer_controller.skip_pomodoro_session(
                work_duration=self.work_duration,
                short_break_duration=self.short_break_duration,
                long_break_duration=self.long_break_duration,
                work_count_down=self.work_count_down,
                short_break_count_down=self.short_break_count_down,
                long_break_count_down=self.long_break_count_down,
            )
            if timer:
                self.start_button.setText("Continue")
                self.start_button.setEnabled(False)
                self.pause_button.setEnabled(True)
                self._update_button_states_for_mode(mode)

                # Update status based on session type
                if timer.pomodoro_session_type == "work":
                    self.status_label.setText(f"Work Session: {self.current_task.name}")
                elif timer.pomodoro_session_type == "short_break":
                    self.status_label.setText("Short Break")
                elif timer.pomodoro_session_type == "long_break":
                    self.status_label.setText("Long Break")

                self.timer_started.emit(timer)

    def reset_timer(self):
        """Reset the timer (for Pomodoro: reset cycle, for others: reset display)."""
        mode = self.get_current_mode()
        if mode == "pomodoro":
            self.timer_controller.reset_pomodoro_cycle()
            self.start_button.setText("Start")
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.skip_button.setEnabled(False)
            self.reset_button.setEnabled(False)
            self.time_label.setText("00:00:00")
            self.status_label.setText("Ready to start")
        else:
            # For stopwatch/countdown, just reset display
            self.time_label.setText("00:00:00")
            self.status_label.setText("Ready to start")

    def _update_button_states_for_mode(self, mode: str):
        """Update button states based on the current timer mode."""
        if mode == "pomodoro":
            # Pomodoro mode: show skip and reset buttons
            self.finish_button.setVisible(False)
            self.skip_button.setVisible(True)
            self.reset_button.setVisible(True)
            self.skip_button.setEnabled(True)
            self.reset_button.setEnabled(True)
        else:
            # Stopwatch/countdown mode: show finish button
            self.finish_button.setVisible(True)
            self.skip_button.setVisible(False)
            self.reset_button.setVisible(False)
            self.finish_button.setEnabled(True)

    def update_display(self):
        """Update the timer display."""
        active_timer = self.timer_controller.get_active_timer()

        # Optimize timer updates - only update frequently when there's an active timer
        has_active_timer = active_timer is not None
        if has_active_timer != self._has_active_timer:
            self._has_active_timer = has_active_timer
            if has_active_timer:
                self.update_timer.start(100)  # Fast updates when timer is running
            else:
                self.update_timer.start(1000)  # Slower updates when no timer

        if active_timer:
            # Check if timer is paused
            is_paused = self.timer_controller.is_timer_paused()
            mode = self.get_current_mode()

            # Calculate elapsed time once to avoid multiple calculations
            if is_paused:
                elapsed_seconds = self.timer_controller.get_elapsed_at_pause()
            else:
                elapsed_seconds = self.timer_controller.get_effective_elapsed_time(
                    active_timer
                )

            elapsed = timedelta(seconds=elapsed_seconds)

            if mode == "pomodoro" and active_timer.duration:
                # Pomodoro mode - check count direction based on session type
                session_type = active_timer.pomodoro_session_type

                # Determine count direction based on session type
                if session_type == "work":
                    count_down = self.work_count_down
                elif session_type == "short_break":
                    count_down = self.short_break_count_down
                elif session_type == "long_break":
                    count_down = self.long_break_count_down
                else:
                    count_down = True  # Default to count down

                if count_down:
                    # Count down mode
                    remaining = active_timer.duration - elapsed.total_seconds()

                    if remaining <= 0:
                        # Timer completed
                        self.finish_timer()
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
                else:
                    # Count up mode
                    elapsed_seconds = elapsed.total_seconds()

                    # Check if we've reached or exceeded the target duration
                    if elapsed_seconds >= active_timer.duration:
                        # Timer completed
                        self.finish_timer()
                        self.timer_completed.emit(active_timer)

                        # Handle Pomodoro session completion
                        self.handle_pomodoro_completion(active_timer)
                        return

                    hours, remainder = divmod(elapsed_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    self.time_label.setText(
                        f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
                    )

                # Update status
                session_type = active_timer.pomodoro_session_type
                status_text = ""
                if session_type == "work":
                    status_text = f"Work Session: {self.current_task.name}"
                elif session_type == "short_break":
                    status_text = "Short Break"
                elif session_type == "long_break":
                    status_text = "Long Break"

                if is_paused:
                    status_text += " (Paused)"

                self.status_label.setText(status_text)

            else:
                # Stopwatch or countdown mode

                if mode == "countdown" and active_timer.duration:
                    # Countdown mode - check count direction
                    if self.countdown_count_down:
                        # Count down mode
                        remaining = active_timer.duration - elapsed.total_seconds()

                        if remaining <= 0:
                            # Timer completed
                            self.finish_timer()
                            self.timer_completed.emit(active_timer)
                            if self.notification_manager:
                                self.notification_manager.show_success(
                                    "Timer Complete", "Your timer has finished!"
                                )
                            else:
                                QMessageBox.information(
                                    self, "Timer Complete", "Your timer has finished!"
                                )
                            return

                        # Display remaining time
                        hours, remainder = divmod(remaining, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        self.time_label.setText(
                            f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
                        )
                    else:
                        # Count up mode
                        elapsed_seconds = elapsed.total_seconds()

                        # Check if we've reached or exceeded the target duration
                        if elapsed_seconds >= active_timer.duration:
                            # Timer completed
                            self.finish_timer()
                            self.timer_completed.emit(active_timer)
                            if self.notification_manager:
                                self.notification_manager.show_success(
                                    "Timer Complete", "Your timer has finished!"
                                )
                            else:
                                QMessageBox.information(
                                    self, "Timer Complete", "Your timer has finished!"
                                )
                            return

                        hours, remainder = divmod(elapsed_seconds, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        self.time_label.setText(
                            f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
                        )
                else:
                    # Stopwatch mode (always count up)
                    hours, remainder = divmod(elapsed.total_seconds(), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    self.time_label.setText(
                        f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
                    )

                # Update status for stopwatch/countdown
                if mode == "stopwatch":
                    status_text = f"Running: {self.current_task.name}"
                elif mode == "countdown":
                    status_text = f"Countdown: {self.current_task.name}"
                else:
                    status_text = f"Running: {self.current_task.name}"

                if is_paused:
                    status_text += " (Paused)"

                self.status_label.setText(status_text)
        else:
            self.time_label.setText("00:00:00")

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
            work_count_down=self.work_count_down,
            short_break_count_down=self.short_break_count_down,
            long_break_count_down=self.long_break_count_down,
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
            work_count_down=self.work_count_down,
            short_break_count_down=self.short_break_count_down,
            long_break_count_down=self.long_break_count_down,
        )
        if timer:
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            break_label = "Short Break" if break_type == "short_break" else "Long Break"
            self.status_label.setText(break_label)
            self.timer_started.emit(timer)

    def open_timer_history(self):
        """Open the timer history dialog."""
        dialog = TimerHistoryDialog(self.db_service, self)
        dialog.exec()

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
