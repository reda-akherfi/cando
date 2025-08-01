"""
Settings widget for the Cando application.

This module provides a comprehensive settings interface with a sidebar menu
for organizing different types of settings.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QGroupBox,
    QFormLayout,
    QSpinBox,
    QCheckBox,
    QComboBox,
    QLineEdit,
    QTextEdit,
    QScrollArea,
    QFrame,
    QSplitter,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon
from typing import Dict, Any
from app.ui.theme_config import ThemeConfigWidget


class SettingsWidget(QWidget):
    """Main settings widget with sidebar navigation."""

    settings_changed = Signal(dict)  # Emits settings changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_settings = {}
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create splitter for sidebar and content
        splitter = QSplitter(Qt.Horizontal)

        # Sidebar
        self.setup_sidebar(splitter)

        # Content area
        self.setup_content_area(splitter)

        # Set splitter proportions
        splitter.setSizes([200, 600])

        layout.addWidget(splitter)

    def setup_sidebar(self, parent):
        """Set up the sidebar navigation."""
        sidebar_frame = QFrame()
        sidebar_frame.setFrameStyle(QFrame.StyledPanel)
        sidebar_frame.setMaximumWidth(250)
        sidebar_frame.setMinimumWidth(180)

        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title_label = QLabel("Settings")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        sidebar_layout.addWidget(title_label)

        # Navigation list
        self.nav_list = QListWidget()
        self.nav_list.setMaximumWidth(230)
        self.nav_list.currentRowChanged.connect(self.on_navigation_changed)

        # Add navigation items
        nav_items = [
            "General",
            "Theme",
            "Timer",
            "Notifications",
            "Data & Backup",
            "About",
        ]

        for item_text in nav_items:
            item = QListWidgetItem(item_text)
            self.nav_list.addItem(item)

        sidebar_layout.addWidget(self.nav_list)
        sidebar_layout.addStretch()

        parent.addWidget(sidebar_frame)

    def setup_content_area(self, parent):
        """Set up the content area with stacked widgets."""
        self.content_stack = QStackedWidget()

        # Create different settings pages
        self.general_page = self.create_general_page()
        self.theme_page = self.create_theme_page()
        self.timer_page = self.create_timer_page()
        self.notifications_page = self.create_notifications_page()
        self.data_backup_page = self.create_data_backup_page()
        self.about_page = self.create_about_page()

        # Add pages to stack
        self.content_stack.addWidget(self.general_page)
        self.content_stack.addWidget(self.theme_page)
        self.content_stack.addWidget(self.timer_page)
        self.content_stack.addWidget(self.notifications_page)
        self.content_stack.addWidget(self.data_backup_page)
        self.content_stack.addWidget(self.about_page)

        parent.addWidget(self.content_stack)

    def create_general_page(self) -> QWidget:
        """Create the general settings page."""
        page = QWidget()
        layout = QVBoxLayout(page)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # Application settings
        app_group = QGroupBox("Application Settings")
        app_layout = QFormLayout(app_group)

        # Start maximized
        self.start_maximized_check = QCheckBox("Start application maximized")
        app_layout.addRow("Startup:", self.start_maximized_check)

        # Auto-save interval
        self.auto_save_spin = QSpinBox()
        self.auto_save_spin.setRange(1, 60)
        self.auto_save_spin.setSuffix(" minutes")
        app_layout.addRow("Auto-save interval:", self.auto_save_spin)

        # Language
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Spanish", "French", "German"])
        app_layout.addRow("Language:", self.language_combo)

        content_layout.addWidget(app_group)

        # Interface settings
        interface_group = QGroupBox("Interface Settings")
        interface_layout = QFormLayout(interface_group)

        # Show tooltips
        self.show_tooltips_check = QCheckBox("Show tooltips")
        self.show_tooltips_check.setChecked(True)
        interface_layout.addRow("Tooltips:", self.show_tooltips_check)

        # Confirm deletions
        self.confirm_deletions_check = QCheckBox("Confirm before deleting items")
        self.confirm_deletions_check.setChecked(True)
        interface_layout.addRow("Confirmations:", self.confirm_deletions_check)

        # Show status bar
        self.show_status_bar_check = QCheckBox("Show status bar")
        self.show_status_bar_check.setChecked(True)
        interface_layout.addRow("Status Bar:", self.show_status_bar_check)

        content_layout.addWidget(interface_group)

        # Performance settings
        perf_group = QGroupBox("Performance Settings")
        perf_layout = QFormLayout(perf_group)

        # Chart update frequency
        self.chart_update_spin = QSpinBox()
        self.chart_update_spin.setRange(1, 60)
        self.chart_update_spin.setSuffix(" seconds")
        self.chart_update_spin.setValue(5)
        perf_layout.addRow("Chart update frequency:", self.chart_update_spin)

        # Cache size
        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(10, 1000)
        self.cache_size_spin.setSuffix(" MB")
        self.cache_size_spin.setValue(100)
        perf_layout.addRow("Cache size:", self.cache_size_spin)

        content_layout.addWidget(perf_group)

        # Action buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_general_settings)
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_general_settings)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()

        content_layout.addLayout(button_layout)
        content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

        return page

    def create_theme_page(self) -> QWidget:
        """Create the theme settings page."""
        page = QWidget()
        layout = QVBoxLayout(page)

        # Add the theme configuration widget
        self.theme_config = ThemeConfigWidget()
        self.theme_config.theme_changed.connect(self.on_theme_changed)
        layout.addWidget(self.theme_config)

        return page

    def create_timer_page(self) -> QWidget:
        """Create the timer settings page."""
        page = QWidget()
        layout = QVBoxLayout(page)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # Default timer settings
        default_group = QGroupBox("Default Timer Settings")
        default_layout = QFormLayout(default_group)

        # Default timer mode
        self.default_timer_mode = QComboBox()
        self.default_timer_mode.addItems(["Stopwatch", "Countdown", "Pomodoro"])
        default_layout.addRow("Default mode:", self.default_timer_mode)

        # Default countdown duration
        self.default_countdown_minutes = QSpinBox()
        self.default_countdown_minutes.setRange(1, 480)
        self.default_countdown_minutes.setSuffix(" minutes")
        self.default_countdown_minutes.setValue(25)
        default_layout.addRow("Default countdown:", self.default_countdown_minutes)

        content_layout.addWidget(default_group)

        # Pomodoro settings
        pomodoro_group = QGroupBox("Pomodoro Settings")
        pomodoro_layout = QFormLayout(pomodoro_group)

        # Work duration
        self.pomodoro_work_duration = QSpinBox()
        self.pomodoro_work_duration.setRange(1, 120)
        self.pomodoro_work_duration.setSuffix(" minutes")
        self.pomodoro_work_duration.setValue(25)
        pomodoro_layout.addRow("Work duration:", self.pomodoro_work_duration)

        # Short break duration
        self.pomodoro_short_break = QSpinBox()
        self.pomodoro_short_break.setRange(1, 30)
        self.pomodoro_short_break.setSuffix(" minutes")
        self.pomodoro_short_break.setValue(5)
        pomodoro_layout.addRow("Short break:", self.pomodoro_short_break)

        # Long break duration
        self.pomodoro_long_break = QSpinBox()
        self.pomodoro_long_break.setRange(5, 60)
        self.pomodoro_long_break.setSuffix(" minutes")
        self.pomodoro_long_break.setValue(15)
        pomodoro_layout.addRow("Long break:", self.pomodoro_long_break)

        # Autostart settings
        self.pomodoro_autostart_breaks = QCheckBox("Auto-start breaks")
        self.pomodoro_autostart_breaks.setChecked(True)
        pomodoro_layout.addRow("Auto-start breaks:", self.pomodoro_autostart_breaks)

        self.pomodoro_autostart_work = QCheckBox("Auto-start work sessions")
        self.pomodoro_autostart_work.setChecked(False)
        pomodoro_layout.addRow("Auto-start work:", self.pomodoro_autostart_work)

        content_layout.addWidget(pomodoro_group)

        # Timer behavior
        behavior_group = QGroupBox("Timer Behavior")
        behavior_layout = QFormLayout(behavior_group)

        # Sound notifications
        self.timer_sound_check = QCheckBox("Play sound when timer completes")
        self.timer_sound_check.setChecked(True)
        behavior_layout.addRow("Sound notifications:", self.timer_sound_check)

        # System notifications
        self.timer_system_notifications = QCheckBox("Show system notifications")
        self.timer_system_notifications.setChecked(True)
        behavior_layout.addRow("System notifications:", self.timer_system_notifications)

        # Keep on top
        self.timer_keep_on_top = QCheckBox("Keep timer window on top")
        self.timer_keep_on_top.setChecked(False)
        behavior_layout.addRow("Keep on top:", self.timer_keep_on_top)

        content_layout.addWidget(behavior_group)

        # Action buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Timer Settings")
        save_btn.clicked.connect(self.save_timer_settings)
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_timer_settings)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()

        content_layout.addLayout(button_layout)
        content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

        return page

    def create_notifications_page(self) -> QWidget:
        """Create the notifications settings page."""
        page = QWidget()
        layout = QVBoxLayout(page)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # Notification types
        types_group = QGroupBox("Notification Types")
        types_layout = QFormLayout(types_group)

        # Success notifications
        self.notify_success = QCheckBox("Show success notifications")
        self.notify_success.setChecked(True)
        types_layout.addRow("Success:", self.notify_success)

        # Error notifications
        self.notify_error = QCheckBox("Show error notifications")
        self.notify_error.setChecked(True)
        types_layout.addRow("Errors:", self.notify_error)

        # Warning notifications
        self.notify_warning = QCheckBox("Show warning notifications")
        self.notify_warning.setChecked(True)
        types_layout.addRow("Warnings:", self.notify_warning)

        # Info notifications
        self.notify_info = QCheckBox("Show info notifications")
        self.notify_info.setChecked(True)
        types_layout.addRow("Info:", self.notify_info)

        content_layout.addWidget(types_group)

        # Notification behavior
        behavior_group = QGroupBox("Notification Behavior")
        behavior_layout = QFormLayout(behavior_group)

        # Auto-hide duration
        self.notify_duration = QSpinBox()
        self.notify_duration.setRange(1, 30)
        self.notify_duration.setSuffix(" seconds")
        self.notify_duration.setValue(5)
        behavior_layout.addRow("Auto-hide duration:", self.notify_duration)

        # Position
        self.notify_position = QComboBox()
        self.notify_position.addItems(
            ["Top-Right", "Top-Left", "Bottom-Right", "Bottom-Left"]
        )
        behavior_layout.addRow("Position:", self.notify_position)

        # Sound
        self.notify_sound = QCheckBox("Play notification sound")
        self.notify_sound.setChecked(True)
        behavior_layout.addRow("Sound:", self.notify_sound)

        content_layout.addWidget(behavior_group)

        # Action buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Notification Settings")
        save_btn.clicked.connect(self.save_notification_settings)
        test_btn = QPushButton("Test Notifications")
        test_btn.clicked.connect(self.test_notifications)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(test_btn)
        button_layout.addStretch()

        content_layout.addLayout(button_layout)
        content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

        return page

    def create_data_backup_page(self) -> QWidget:
        """Create the data and backup settings page."""
        page = QWidget()
        layout = QVBoxLayout(page)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # Data management
        data_group = QGroupBox("Data Management")
        data_layout = QFormLayout(data_group)

        # Auto-backup
        self.auto_backup_check = QCheckBox("Enable automatic backups")
        self.auto_backup_check.setChecked(True)
        data_layout.addRow("Auto-backup:", self.auto_backup_check)

        # Backup frequency
        self.backup_frequency = QComboBox()
        self.backup_frequency.addItems(["Daily", "Weekly", "Monthly"])
        data_layout.addRow("Backup frequency:", self.backup_frequency)

        # Backup location
        self.backup_location = QLineEdit()
        self.backup_location.setPlaceholderText("Select backup location...")
        data_layout.addRow("Backup location:", self.backup_location)

        # Backup button
        backup_btn = QPushButton("Create Backup Now")
        backup_btn.clicked.connect(self.create_backup)
        data_layout.addRow("", backup_btn)

        content_layout.addWidget(data_group)

        # Data export/import
        export_group = QGroupBox("Export & Import")
        export_layout = QFormLayout(export_group)

        # Export button
        export_btn = QPushButton("Export Data")
        export_btn.clicked.connect(self.export_data)
        export_layout.addRow("Export:", export_btn)

        # Import button
        import_btn = QPushButton("Import Data")
        import_btn.clicked.connect(self.import_data)
        export_layout.addRow("Import:", import_btn)

        content_layout.addWidget(export_group)

        # Data cleanup
        cleanup_group = QGroupBox("Data Cleanup")
        cleanup_layout = QFormLayout(cleanup_group)

        # Clear all data button
        clear_btn = QPushButton("Clear All Data")
        clear_btn.clicked.connect(self.clear_all_data)
        clear_btn.setProperty("class", "danger-button")
        cleanup_layout.addRow("Clear data:", clear_btn)

        # Reset to sample data button
        sample_btn = QPushButton("Reset to Sample Data")
        sample_btn.clicked.connect(self.reset_to_sample_data)
        cleanup_layout.addRow("Reset to sample:", sample_btn)

        content_layout.addWidget(cleanup_group)

        content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

        return page

    def create_about_page(self) -> QWidget:
        """Create the about page."""
        page = QWidget()
        layout = QVBoxLayout(page)

        # About information
        about_group = QGroupBox("About Cando")
        about_layout = QVBoxLayout(about_group)

        # App name and version
        app_info = QLabel("Cando - Productivity Application")
        app_info.setFont(QFont("Segoe UI", 18, QFont.Bold))
        app_info.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(app_info)

        version_info = QLabel("Version 1.0.0")
        version_info.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(version_info)

        # Description
        description = QTextEdit()
        description.setMaximumHeight(100)
        description.setPlainText(
            "Cando is a comprehensive productivity application that helps you "
            "manage projects, tasks, and time effectively. Features include "
            "project management, task tracking, Pomodoro timer, and detailed analytics."
        )
        description.setReadOnly(True)
        about_layout.addWidget(description)

        # System information
        system_group = QGroupBox("System Information")
        system_layout = QFormLayout(system_group)

        # Python version
        import sys

        python_version = QLabel(sys.version)
        system_layout.addRow("Python version:", python_version)

        # PySide6 version
        try:
            import PySide6

            pyside_version = QLabel(PySide6.__version__)
        except:
            pyside_version = QLabel("Unknown")
        system_layout.addRow("PySide6 version:", pyside_version)

        # Database info
        db_info = QLabel("SQLite")
        system_layout.addRow("Database:", db_info)

        about_layout.addWidget(system_group)

        layout.addWidget(about_group)
        layout.addStretch()

        return page

    def on_navigation_changed(self, index: int):
        """Handle navigation change."""
        self.content_stack.setCurrentIndex(index)

    def on_theme_changed(self, theme_config: Dict[str, Any]):
        """Handle theme configuration changes."""
        self.settings_changed.emit({"type": "theme", "config": theme_config})

    def save_general_settings(self):
        """Save general settings."""
        settings = {
            "start_maximized": self.start_maximized_check.isChecked(),
            "auto_save_interval": self.auto_save_spin.value(),
            "language": self.language_combo.currentText(),
            "show_tooltips": self.show_tooltips_check.isChecked(),
            "confirm_deletions": self.confirm_deletions_check.isChecked(),
            "show_status_bar": self.show_status_bar_check.isChecked(),
            "chart_update_frequency": self.chart_update_spin.value(),
            "cache_size": self.cache_size_spin.value(),
        }
        self.settings_changed.emit({"type": "general", "config": settings})

    def reset_general_settings(self):
        """Reset general settings to defaults."""
        self.start_maximized_check.setChecked(False)
        self.auto_save_spin.setValue(5)
        self.language_combo.setCurrentText("English")
        self.show_tooltips_check.setChecked(True)
        self.confirm_deletions_check.setChecked(True)
        self.show_status_bar_check.setChecked(True)
        self.chart_update_spin.setValue(5)
        self.cache_size_spin.setValue(100)

    def save_timer_settings(self):
        """Save timer settings."""
        settings = {
            "default_mode": self.default_timer_mode.currentText().lower(),
            "default_countdown_minutes": self.default_countdown_minutes.value(),
            "pomodoro_work_duration": self.pomodoro_work_duration.value(),
            "pomodoro_short_break": self.pomodoro_short_break.value(),
            "pomodoro_long_break": self.pomodoro_long_break.value(),
            "pomodoro_autostart_breaks": self.pomodoro_autostart_breaks.isChecked(),
            "pomodoro_autostart_work": self.pomodoro_autostart_work.isChecked(),
            "sound_notifications": self.timer_sound_check.isChecked(),
            "system_notifications": self.timer_system_notifications.isChecked(),
            "keep_on_top": self.timer_keep_on_top.isChecked(),
        }
        self.settings_changed.emit({"type": "timer", "config": settings})

    def reset_timer_settings(self):
        """Reset timer settings to defaults."""
        self.default_timer_mode.setCurrentText("Stopwatch")
        self.default_countdown_minutes.setValue(25)
        self.pomodoro_work_duration.setValue(25)
        self.pomodoro_short_break.setValue(5)
        self.pomodoro_long_break.setValue(15)
        self.pomodoro_autostart_breaks.setChecked(True)
        self.pomodoro_autostart_work.setChecked(False)
        self.timer_sound_check.setChecked(True)
        self.timer_system_notifications.setChecked(True)
        self.timer_keep_on_top.setChecked(False)

    def save_notification_settings(self):
        """Save notification settings."""
        settings = {
            "notify_success": self.notify_success.isChecked(),
            "notify_error": self.notify_error.isChecked(),
            "notify_warning": self.notify_warning.isChecked(),
            "notify_info": self.notify_info.isChecked(),
            "duration": self.notify_duration.value(),
            "position": self.notify_position.currentText(),
            "sound": self.notify_sound.isChecked(),
        }
        self.settings_changed.emit({"type": "notifications", "config": settings})

    def test_notifications(self):
        """Test notification system."""
        # This will be implemented to test different notification types
        pass

    def create_backup(self):
        """Create a data backup."""
        # This will be implemented to create backups
        pass

    def export_data(self):
        """Export application data."""
        # This will be implemented to export data
        pass

    def import_data(self):
        """Import application data."""
        # This will be implemented to import data
        pass

    def clear_all_data(self):
        """Clear all application data."""
        # This will be implemented to clear data
        pass

    def reset_to_sample_data(self):
        """Reset to sample data."""
        # This will be implemented to reset to sample data
        pass

    def load_settings(self):
        """Load current settings into the UI."""
        # This will be implemented to load settings from database
        pass

    def get_settings(self) -> Dict[str, Any]:
        """Get all current settings."""
        return self.current_settings

    def set_settings(self, settings: Dict[str, Any]):
        """Set settings from external source."""
        self.current_settings = settings
        self.load_settings()
