"""
Main window view for the Cando application.

This module contains the main window class that manages the application's
primary user interface with tabbed views for different functionality.
"""

from typing import List
from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QWidget,
    QMessageBox,
    QComboBox,
    QApplication,
    QLineEdit,
    QInputDialog,
    QCheckBox,
    QDialog,
    QScrollArea,
    QStackedWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QShortcut, QKeySequence
from app.ui.chart_widget import (
    TimeByProjectChart,
    DailyProductivityChart,
    TimerTypeChart,
    CumulativeWorkChart,
    TagDistributionChart,
    ProjectDistributionChart,
)
from app.ui.theme import DarkTheme, LightTheme
from app.ui.project_dialog import ProjectDialog
from app.ui.project_list_widget import ProjectListWidget
from app.ui.task_dialog import TaskDialog
from app.ui.task_list_widget import TaskListWidget
from app.ui.tag_dialog import TagDialog
from app.ui.tag_list_widget import TagListWidget
from app.ui.timer_widget import TimerWidget
from app.ui.notification_widget import NotificationManager
from app.ui.settings_widget import SettingsWidget
from app.ui.checklist_filter import ChecklistFilterWidget
from app.ui.ui_main import UiMainWindow
from app.models.project import Project
from app.models.task import Task
from app.models.timer import Timer
from app.services.database import DatabaseService
from app.services.analytics import AnalyticsService
from app.controllers.timer_controller import TimerController
from app.utils.fuzzy_search import fuzzy_search
from app.models.tag import Tag


class MainWindow(QMainWindow):
    """
    Main window for the Cando productivity application.

    Provides a tabbed interface with Dashboard, Projects, Timer, and Settings views.
    """

    def __init__(
        self,
        db_service: DatabaseService,
        analytics_service: AnalyticsService,
        timer_controller: TimerController,
    ):
        """
        Initialize the main window with tabbed interface.

        Args:
            db_service: Database service for data access
            analytics_service: Analytics service for data analysis
            timer_controller: Timer controller for timer operations
        """
        super().__init__()
        self.db_service = db_service
        self.analytics_service = analytics_service
        self.timer_controller = timer_controller
        self.is_dark_theme = True  # Track current theme
        self._sync_in_progress = False  # Flag to prevent recursive synchronization

        self.ui = UiMainWindow()
        self.ui.setupUi(self)

        # Initialize notification manager
        self.notification_manager = NotificationManager(self)

        self.setup_tabs()

        # Load and apply theme during initialization
        theme_config = self.db_service.load_theme_settings()
        if not theme_config:
            # Use default dark theme if no theme is found
            theme_config = {
                "name": "Custom Theme",
                "colors": {
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
                    # Priority colors
                    "priority_low": "#00ff00",
                    "priority_medium": "#ffff00",
                    "priority_high": "#ff8800",
                    "priority_critical": "#ff0000",
                    # Status colors
                    "status_active": "#00ff00",
                    "status_in_progress": "#00aaff",
                    "status_on_hold": "#ffff00",
                    "status_completed": "#00ff00",
                    "status_cancelled": "#ff0000",
                },
                "fonts": {
                    "base_size": 14,
                    "title_size": 18,
                    "subtitle_size": 16,
                    "font_family": "Segoe UI",
                },
                "spacing": {"padding": 8, "margin": 4, "border_radius": 4},
            }

        self.apply_theme_from_config(theme_config)

        self.refresh_data()

    def setup_tabs(self):
        """Set up the tabbed interface with different application views."""
        self.tab_widget = QTabWidget()

        # Create tab content
        self.dashboard_tab = QWidget()
        self.projects_tab = QWidget()
        self.tags_tab = QWidget()
        self.timer_tab = QWidget()
        self.settings_tab = QWidget()

        # Add tabs
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        self.tab_widget.addTab(self.projects_tab, "Projects")
        self.tab_widget.addTab(self.tags_tab, "Tags")
        self.tab_widget.addTab(self.timer_tab, "Timer")
        self.tab_widget.addTab(self.settings_tab, "Settings")

        # Set up tab layouts
        self.setup_dashboard_tab()
        self.setup_projects_tab()
        self.setup_tags_tab()
        self.setup_timer_tab()
        self.setup_settings_tab()

        # Add tab widget to main layout
        self.ui.layout.addWidget(self.tab_widget)

    def setup_dashboard_tab(self):
        """Set up the dashboard tab with charts and analytics."""
        layout = QVBoxLayout(self.dashboard_tab)

        # Create chart widgets
        self.project_chart = TimeByProjectChart()
        self.productivity_chart = DailyProductivityChart()
        self.timer_type_chart = TimerTypeChart()
        self.cumulative_work_chart = CumulativeWorkChart()
        self.tag_distribution_chart = TagDistributionChart()
        self.project_distribution_chart = ProjectDistributionChart()

        # Create navigation controls
        nav_layout = QHBoxLayout()

        # Chart title label
        self.chart_title_label = QLabel("Time by Project")
        self.chart_title_label.setAlignment(Qt.AlignCenter)
        self.chart_title_label.setProperty("class", "chart-title")

        # Create refresh button
        refresh_button = QPushButton("Refresh Charts")
        refresh_button.clicked.connect(self.refresh_charts)

        # Navigation arrows (grouped together)
        arrows_layout = QHBoxLayout()
        arrows_layout.setSpacing(5)  # Small spacing between arrows

        # Left arrow button
        self.prev_chart_btn = QPushButton("←")
        self.prev_chart_btn.setMaximumWidth(50)
        self.prev_chart_btn.clicked.connect(self.show_previous_chart)
        self.prev_chart_btn.setToolTip("Previous Chart")

        # Right arrow button
        self.next_chart_btn = QPushButton("→")
        self.next_chart_btn.setMaximumWidth(50)
        self.next_chart_btn.clicked.connect(self.show_next_chart)
        self.next_chart_btn.setToolTip("Next Chart")

        arrows_layout.addWidget(self.prev_chart_btn)
        arrows_layout.addWidget(self.next_chart_btn)

        # Group all buttons together on the right
        nav_layout.addWidget(self.chart_title_label)
        nav_layout.addStretch()  # Push everything to the right
        nav_layout.addWidget(refresh_button)
        nav_layout.addLayout(arrows_layout)

        # Create stacked widget for charts
        self.chart_stack = QStackedWidget()
        self.chart_stack.addWidget(self.project_chart)
        self.chart_stack.addWidget(self.productivity_chart)
        self.chart_stack.addWidget(self.timer_type_chart)
        self.chart_stack.addWidget(self.cumulative_work_chart)
        self.chart_stack.addWidget(self.tag_distribution_chart)
        self.chart_stack.addWidget(self.project_distribution_chart)

        # Chart titles for navigation
        self.chart_titles = [
            "Time by Project",
            "Daily Productivity",
            "Timer Type Usage",
            "Cumulative Work Hours",
            "Tag Distribution",
            "Project Distribution",
        ]
        self.current_chart_index = 0

        # Add widgets to layout
        layout.addLayout(nav_layout)
        layout.addWidget(self.chart_stack)

        # Update navigation buttons state
        self.update_navigation_buttons()

    def setup_projects_tab(self):
        """Set up the projects tab for project and task management."""
        layout = QVBoxLayout(self.projects_tab)

        # Main horizontal layout for projects (left) and tasks (right)
        main_layout = QHBoxLayout()

        # Left side - Projects
        projects_layout = QVBoxLayout()

        # Project management controls
        controls_layout = QHBoxLayout()

        # Search functionality
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search projects by name, description, or tags... (Ctrl+F)"
        )
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.search_input.setMaximumWidth(165)  # 45% less than 300

        # Add keyboard shortcuts
        from PySide6.QtGui import QKeySequence, QShortcut

        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(self.focus_search)

        # Add Escape key to clear search
        escape_shortcut = QShortcut(QKeySequence("Escape"), self.search_input)
        escape_shortcut.activated.connect(self.clear_search)

        # Add clear button
        self.clear_search_btn = QPushButton("Clear")
        self.clear_search_btn.clicked.connect(self.clear_search)
        self.clear_search_btn.setMaximumWidth(70)

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.clear_search_btn)

        controls_layout.addLayout(search_layout)

        # Filter controls
        # Status filter
        self.status_filter = ChecklistFilterWidget("Status")
        self.status_filter.set_items(self.get_all_project_statuses())
        self.status_filter.set_selection_changed_callback(self.refresh_project_list)

        # Priority filter
        self.priority_filter = ChecklistFilterWidget("Priority")
        self.priority_filter.set_items(self.get_all_project_priorities())
        self.priority_filter.set_selection_changed_callback(self.refresh_project_list)

        # Tag filter
        self.tag_filter = ChecklistFilterWidget("Tag")
        self.tag_filter.set_items([])  # Will be populated later
        self.tag_filter.set_selection_changed_callback(self.refresh_project_list)

        controls_layout.addWidget(self.status_filter)
        controls_layout.addWidget(self.priority_filter)
        controls_layout.addWidget(self.tag_filter)
        controls_layout.addStretch()

        # Action buttons
        self.add_project_btn = QPushButton("+")
        self.add_project_btn.clicked.connect(self.add_project)
        self.add_project_btn.setMaximumWidth(
            50
        )  # Slightly larger to accommodate bigger + sign
        self.add_project_btn.setToolTip("Add Project")
        # Make the + sign larger using inline stylesheet to override global styles
        self.add_project_btn.setStyleSheet("font-size: 24px; font-weight: bold;")

        controls_layout.addWidget(self.add_project_btn)

        projects_layout.addLayout(controls_layout)

        # Search results counter
        self.search_results_label = QLabel("")
        self.search_results_label.setProperty("class", "secondary-text")
        projects_layout.addWidget(self.search_results_label)

        # Project list
        self.project_list_widget = ProjectListWidget()
        self.project_list_widget.project_edit_requested.connect(self.edit_project)
        self.project_list_widget.project_delete_requested.connect(self.delete_project)
        self.project_list_widget.project_selected.connect(self.on_project_selected)

        projects_layout.addWidget(self.project_list_widget)

        # Right side - Tasks
        tasks_layout = QVBoxLayout()

        # Task search and filter functionality
        task_controls_layout = QHBoxLayout()

        # Task search
        self.task_search_input = QLineEdit()
        self.task_search_input.setPlaceholderText(
            "Search tasks by name, description, or tags... (Ctrl+Shift+F)"
        )
        self.task_search_input.textChanged.connect(self.on_task_search_text_changed)
        self.task_search_input.setMaximumWidth(165)  # 45% less than 300
        self.task_search_input.setEnabled(False)  # Disabled until project is selected

        # Add keyboard shortcuts for task search
        task_search_shortcut = QShortcut(QKeySequence("Ctrl+Shift+F"), self)
        task_search_shortcut.activated.connect(self.focus_task_search)

        # Add Escape key to clear task search
        task_escape_shortcut = QShortcut(QKeySequence("Escape"), self.task_search_input)
        task_escape_shortcut.activated.connect(self.clear_task_search)

        # Add clear button for task search
        self.clear_task_search_btn = QPushButton("Clear")
        self.clear_task_search_btn.clicked.connect(self.clear_task_search)
        self.clear_task_search_btn.setMaximumWidth(70)
        self.clear_task_search_btn.setEnabled(
            False
        )  # Disabled until project is selected

        task_search_layout = QHBoxLayout()
        task_search_layout.addWidget(self.task_search_input)
        task_search_layout.addWidget(self.clear_task_search_btn)

        task_controls_layout.addLayout(task_search_layout)

        # Task filters
        # Task status filter
        self.task_status_filter = ChecklistFilterWidget("Status")
        self.task_status_filter.set_items(self.get_all_task_statuses())
        self.task_status_filter.set_selection_changed_callback(
            self.on_task_filter_changed
        )
        self.task_status_filter.setEnabled(False)  # Disabled until project is selected

        # Task priority filter
        self.task_priority_filter = ChecklistFilterWidget("Priority")
        self.task_priority_filter.set_items(self.get_all_task_priorities())
        self.task_priority_filter.set_selection_changed_callback(
            self.on_task_filter_changed
        )
        self.task_priority_filter.setEnabled(
            False
        )  # Disabled until project is selected

        # Task tag filter
        self.task_tag_filter = ChecklistFilterWidget("Tag")
        self.task_tag_filter.set_items([])  # Will be populated later
        self.task_tag_filter.set_selection_changed_callback(self.on_task_filter_changed)
        self.task_tag_filter.setEnabled(False)  # Disabled until project is selected

        task_controls_layout.addWidget(self.task_status_filter)
        task_controls_layout.addWidget(self.task_priority_filter)
        task_controls_layout.addWidget(self.task_tag_filter)
        task_controls_layout.addStretch()

        # Add task button
        self.add_task_btn = QPushButton("+")
        self.add_task_btn.clicked.connect(self.add_task)
        self.add_task_btn.setMaximumWidth(
            50
        )  # Slightly larger to accommodate bigger + sign
        self.add_task_btn.setToolTip("Add Task")
        self.add_task_btn.setEnabled(False)  # Disabled until project is selected
        # Make the + sign larger using inline stylesheet to override global styles
        self.add_task_btn.setStyleSheet("font-size: 24px; font-weight: bold;")

        task_controls_layout.addWidget(self.add_task_btn)

        tasks_layout.addLayout(task_controls_layout)

        # Task search results counter
        self.task_search_results_label = QLabel("")
        self.task_search_results_label.setProperty("class", "secondary-text")
        tasks_layout.addWidget(self.task_search_results_label)

        # Task list
        self.task_list_widget = TaskListWidget()
        self.task_list_widget.task_edit_requested.connect(self.edit_task)
        self.task_list_widget.task_delete_requested.connect(self.delete_task)
        self.task_list_widget.task_selected.connect(self.on_task_selected)

        tasks_layout.addWidget(self.task_list_widget)

        # Add both sides to the main horizontal layout
        main_layout.addLayout(projects_layout)
        main_layout.addLayout(tasks_layout)

        # Add the main layout to the tab
        layout.addLayout(main_layout)

    def setup_timer_tab(self):
        """Set up the timer tab with comprehensive timer widget."""
        layout = QVBoxLayout(self.timer_tab)

        # Create scroll area for the timer widget
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Create and add the comprehensive timer widget
        self.timer_widget = TimerWidget(
            self.timer_controller, self.db_service, self.notification_manager
        )
        scroll_area.setWidget(self.timer_widget)
        layout.addWidget(scroll_area)

        # Connect timer widget signals
        self.timer_widget.timer_started.connect(self.on_timer_started)
        self.timer_widget.timer_stopped.connect(self.on_timer_stopped)
        self.timer_widget.timer_completed.connect(self.on_timer_completed)

        # Connect synchronization signals
        self.timer_widget.project_selected.connect(self.on_timer_project_selected)
        self.timer_widget.task_selected.connect(self.on_timer_task_selected)

    def setup_settings_tab(self):
        """Set up the settings tab for application configuration."""
        layout = QVBoxLayout(self.settings_tab)

        # Create the settings widget
        self.settings_widget = SettingsWidget()
        self.settings_widget.settings_changed.connect(self.on_settings_changed)

        # Load current settings
        self.load_settings_into_widget()

        layout.addWidget(self.settings_widget)

    def setup_tags_tab(self):
        """Set up the tags tab for managing tags."""
        layout = QVBoxLayout(self.tags_tab)

        # Top controls layout with Add Tag button on the right
        top_controls_layout = QHBoxLayout()

        # Search and sort controls
        controls_layout = QHBoxLayout()

        # Search functionality
        search_label = QLabel("Search Tags:")
        self.tag_search_input = QLineEdit()
        self.tag_search_input.setPlaceholderText("Search tags by name... (Ctrl+T)")
        self.tag_search_input.textChanged.connect(self.on_tag_search_text_changed)
        self.tag_search_input.setMinimumWidth(300)

        # Add keyboard shortcut for tag search
        tag_search_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        tag_search_shortcut.activated.connect(self.focus_tag_search)

        # Add Escape key to clear tag search
        tag_escape_shortcut = QShortcut(QKeySequence("Escape"), self.tag_search_input)
        tag_escape_shortcut.activated.connect(self.clear_tag_search)

        # Add clear button for tag search
        self.clear_tag_search_btn = QPushButton("Clear")
        self.clear_tag_search_btn.clicked.connect(self.clear_tag_search)
        self.clear_tag_search_btn.setMaximumWidth(70)

        # Sort controls
        sort_label = QLabel("Sort by:")
        self.tag_sort_combo = QComboBox()
        self.tag_sort_combo.addItems(
            [
                "Name (A-Z)",
                "Name (Z-A)",
                "Popularity (High-Low)",
                "Popularity (Low-High)",
            ]
        )
        self.tag_sort_combo.currentTextChanged.connect(self.on_tag_sort_changed)

        controls_layout.addWidget(search_label)
        controls_layout.addWidget(self.tag_search_input)
        controls_layout.addWidget(self.clear_tag_search_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(sort_label)
        controls_layout.addWidget(self.tag_sort_combo)

        # Add Tag button positioned on the right
        self.add_tag_btn = QPushButton("Add Tag")
        self.add_tag_btn.clicked.connect(self.add_tag)

        # Add controls to top layout with Add Tag button on the right
        top_controls_layout.addLayout(controls_layout)
        top_controls_layout.addWidget(self.add_tag_btn)

        layout.addLayout(top_controls_layout)

        # Tag search results counter
        self.tag_search_results_label = QLabel("")
        self.tag_search_results_label.setProperty("class", "secondary-text")
        layout.addWidget(self.tag_search_results_label)

        # Tag list
        self.tag_list_widget = TagListWidget()
        self.tag_list_widget.tag_edit_requested.connect(self.edit_tag)
        self.tag_list_widget.tag_delete_requested.connect(self.delete_tag)
        self.tag_list_widget.tag_selected.connect(self.on_tag_selected)
        layout.addWidget(self.tag_list_widget)

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        app = QApplication.instance()

        if self.is_dark_theme:
            # Switch to light theme
            LightTheme.apply_to_application(app)
            self.theme_button.setText("Switch to Dark Mode")
            self.is_dark_theme = False
        else:
            # Switch to dark theme
            DarkTheme.apply_to_application(app)
            self.theme_button.setText("Switch to Light Mode")
            self.is_dark_theme = True

        # Refresh charts to update their appearance
        self.refresh_charts()

    def on_maximized_setting_changed(self, checked: bool):
        """Handle changes to the maximized setting."""
        self.db_service.set_config("always_maximized", "true" if checked else "false")

    def on_settings_changed(self, settings_data: dict):
        """Handle settings changes from the settings widget."""
        settings_type = settings_data.get("type")
        config = settings_data.get("config", {})

        if settings_type == "theme":
            self.apply_custom_theme(config)
        elif settings_type == "general":
            self.db_service.save_general_settings(config)
        elif settings_type == "timer":
            self.db_service.save_timer_settings(config)
        elif settings_type == "notifications":
            self.db_service.save_notification_settings(config)

        # Show success notification
        if self.notification_manager:
            self.notification_manager.show_success(
                "Settings Saved", "Your settings have been saved successfully!"
            )

    def load_settings_into_widget(self):
        """Load current settings into the settings widget."""
        # Load theme settings
        theme_config = self.db_service.load_theme_settings()
        if theme_config and hasattr(self.settings_widget, "theme_config"):
            self.settings_widget.theme_config.set_theme_config(theme_config)

        # Load general settings
        general_settings = self.db_service.load_general_settings()
        if hasattr(self.settings_widget, "start_maximized_check"):
            self.settings_widget.start_maximized_check.setChecked(
                general_settings.get("start_maximized", False)
            )
            self.settings_widget.auto_save_spin.setValue(
                general_settings.get("auto_save_interval", 5)
            )
            self.settings_widget.language_combo.setCurrentText(
                general_settings.get("language", "English")
            )
            self.settings_widget.show_tooltips_check.setChecked(
                general_settings.get("show_tooltips", True)
            )
            self.settings_widget.confirm_deletions_check.setChecked(
                general_settings.get("confirm_deletions", True)
            )
            self.settings_widget.show_status_bar_check.setChecked(
                general_settings.get("show_status_bar", True)
            )
            self.settings_widget.chart_update_spin.setValue(
                general_settings.get("chart_update_frequency", 5)
            )
            self.settings_widget.cache_size_spin.setValue(
                general_settings.get("cache_size", 100)
            )

        # Load notification settings
        notification_settings = self.db_service.load_notification_settings()
        if hasattr(self.settings_widget, "notify_success"):
            self.settings_widget.notify_success.setChecked(
                notification_settings.get("notify_success", True)
            )
            self.settings_widget.notify_error.setChecked(
                notification_settings.get("notify_error", True)
            )
            self.settings_widget.notify_warning.setChecked(
                notification_settings.get("notify_warning", True)
            )
            self.settings_widget.notify_info.setChecked(
                notification_settings.get("notify_info", True)
            )
            self.settings_widget.notify_duration.setValue(
                notification_settings.get("duration", 5)
            )
            self.settings_widget.notify_position.setCurrentText(
                notification_settings.get("position", "Top-Right")
            )
            self.settings_widget.notify_sound.setChecked(
                notification_settings.get("sound", True)
            )

    def apply_custom_theme(self, theme_config: dict):
        """Apply a custom theme configuration."""
        try:
            # Save theme to database
            self.db_service.save_theme_settings(theme_config)

            # Apply theme to application
            self.apply_theme_from_config(theme_config)

        except Exception as e:
            print(f"Error applying custom theme: {e}")
            if self.notification_manager:
                self.notification_manager.show_error(
                    "Theme Error", f"Failed to apply theme: {str(e)}"
                )

    def apply_theme_from_config(self, theme_config: dict):
        """Apply theme from configuration dictionary."""
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtGui import QPalette, QColor

            app = QApplication.instance()
            if not app:
                return

            # Create palette from theme config
            palette = QPalette()
            colors = theme_config.get("colors", {})

            # Apply colors to palette
            if "window" in colors:
                palette.setColor(QPalette.Window, QColor(colors["window"]))
            if "text" in colors:
                palette.setColor(QPalette.WindowText, QColor(colors["text"]))
            if "base" in colors:
                palette.setColor(QPalette.Base, QColor(colors["base"]))
            if "text" in colors:
                palette.setColor(QPalette.Text, QColor(colors["text"]))
            if "button" in colors:
                palette.setColor(QPalette.Button, QColor(colors["button"]))
            if "button_text" in colors:
                palette.setColor(QPalette.ButtonText, QColor(colors["button_text"]))
            if "highlight" in colors:
                palette.setColor(QPalette.Highlight, QColor(colors["highlight"]))
            if "highlighted_text" in colors:
                palette.setColor(
                    QPalette.HighlightedText, QColor(colors["highlighted_text"])
                )

            # Apply palette to application
            app.setPalette(palette)

            # Apply custom stylesheet if available
            self.apply_custom_stylesheet(theme_config)

        except Exception as e:
            print(f"Error applying theme from config: {e}")

    def apply_custom_stylesheet(self, theme_config: dict):
        """Apply custom stylesheet based on theme configuration."""
        try:
            from PySide6.QtWidgets import QApplication

            app = QApplication.instance()
            if not app:
                return

            colors = theme_config.get("colors", {})
            fonts = theme_config.get("fonts", {})
            spacing = theme_config.get("spacing", {})

            # Build custom stylesheet
            stylesheet = f"""
            QMainWindow {{
                background-color: {colors.get('window', '#1e1e1e')};
                color: {colors.get('text', '#cccccc')};
            }}
            
            QTabWidget::pane {{
                border: 1px solid {colors.get('mid', '#2d2d30')};
                background-color: {colors.get('base', '#2d2d30')};
            }}
            
            QTabBar::tab {{
                background-color: {colors.get('button', '#3c3c3c')};
                color: {colors.get('text', '#cccccc')};
                padding: {spacing.get('padding', 8)}px {spacing.get('padding', 8) * 2}px;
                margin-right: 2px;
                border-top-left-radius: {spacing.get('border_radius', 4)}px;
                border-top-right-radius: {spacing.get('border_radius', 4)}px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {colors.get('highlight', '#0078d4')};
                color: {colors.get('highlighted_text', '#ffffff')};
            }}
            
            QTabBar::tab:hover {{
                background-color: {colors.get('light', '#4c4c4c')};
            }}
            
            QPushButton {{
                background-color: {colors.get('button', '#3c3c3c')};
                color: {colors.get('text', '#cccccc')};
                border: 1px solid {colors.get('mid', '#2d2d30')};
                padding: {spacing.get('padding', 8)}px {spacing.get('padding', 8) * 2}px;
                border-radius: {spacing.get('border_radius', 4)}px;
                font-size: {fonts.get('base_size', 14)}px;
                font-weight: normal;
                outline: none;
                margin: 1px;
                min-height: 20px;
                text-align: center;
            }}
            
            QPushButton:hover {{
                background-color: {colors.get('light', '#4c4c4c')};
                border-color: {colors.get('highlight', '#0078d4')};
            }}
            
            QPushButton:pressed {{
                background-color: {colors.get('dark', '#1e1e1e')};
                border-color: {colors.get('highlight', '#0078d4')};
            }}
            
            QPushButton:disabled {{
                background-color: {colors.get('dark', '#1e1e1e')};
                color: {colors.get('mid', '#2d2d30')};
                border-color: {colors.get('dark', '#1e1e1e')};
            }}
            
            QLabel {{
                color: {colors.get('text', '#cccccc')};
                background-color: transparent;
                font-size: {fonts.get('base_size', 14)}px;
            }}
            
            QLabel[class="secondary-text"] {{
                color: #888888;
                font-size: 11px;
            }}
            
            QLabel[class="time-display"] {{
                color: {colors.get('highlight', '#0078d4')};
                font-size: 48px;
                font-weight: bold;
            }}
            
            QLabel[class="chart-title"] {{
                color: {colors.get('text', '#cccccc')};
                font-size: 16px;
                font-weight: bold;
                margin: 10px;
            }}
            
            QListWidget {{
                background-color: {colors.get('base', '#2d2d30')};
                color: {colors.get('text', '#cccccc')};
                border: 1px solid {colors.get('mid', '#2d2d30')};
                border-radius: {spacing.get('border_radius', 4)}px;
                padding: {spacing.get('margin', 4)}px;
                alternate-background-color: {colors.get('alternate_base', '#252526')};
            }}
            
            QListWidget::item {{
                padding: 6px;
                border-radius: 2px;
                color: {colors.get('text', '#cccccc')};
                background-color: transparent;
            }}
            
            QListWidget::item:selected {{
                background-color: {colors.get('highlight', '#0078d4')};
                color: {colors.get('highlighted_text', '#ffffff')};
            }}
            
            QListWidget::item:hover {{
                background-color: {colors.get('light', '#4c4c4c')};
            }}
            
            QLineEdit {{
                background-color: {colors.get('base', '#2d2d30')};
                color: {colors.get('text', '#cccccc')};
                border: 1px solid {colors.get('light', '#4c4c4c')};
                border-radius: {spacing.get('border_radius', 4)}px;
                padding: {spacing.get('margin', 4)}px;
                font-size: {fonts.get('base_size', 14)}px;
            }}
            
            QLineEdit:hover {{
                border-color: {colors.get('highlight', '#0078d4')};
            }}
            
            QLineEdit:focus {{
                border-color: {colors.get('highlight', '#0078d4')};
                border-width: 2px;
            }}
            
            QComboBox {{
                background-color: {colors.get('base', '#2d2d30')};
                color: {colors.get('text', '#cccccc')};
                border: 1px solid {colors.get('light', '#4c4c4c')};
                border-radius: {spacing.get('border_radius', 4)}px;
                padding: {spacing.get('margin', 4)}px;
                font-size: {fonts.get('base_size', 14)}px;
            }}
            
            QComboBox:hover {{
                border-color: {colors.get('highlight', '#0078d4')};
            }}
            
            QComboBox:focus {{
                border-color: {colors.get('highlight', '#0078d4')};
                border-width: 2px;
            }}
            
            QComboBox::drop-down {{
                border: 1px solid {colors.get('light', '#4c4c4c')};
                border-radius: 2px;
                width: 20px;
                background-color: {colors.get('button', '#3c3c3c')};
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {colors.get('text', '#cccccc')};
                margin-right: 6px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {colors.get('base', '#2d2d30')};
                color: {colors.get('text', '#cccccc')};
                border: 1px solid {colors.get('mid', '#2d2d30')};
                selection-background-color: {colors.get('highlight', '#0078d4')};
                selection-color: {colors.get('highlighted_text', '#ffffff')};
                outline: none;
            }}
            
            QComboBox QAbstractItemView::item {{
                background-color: {colors.get('base', '#2d2d30')};
                color: {colors.get('text', '#cccccc')};
                padding: 8px;
            }}
            
            QComboBox QAbstractItemView::item:hover {{
                background-color: {colors.get('light', '#4c4c4c')};
                color: {colors.get('text', '#cccccc')};
            }}
            
            QComboBox QAbstractItemView::item:selected {{
                background-color: {colors.get('highlight', '#0078d4')};
                color: {colors.get('highlighted_text', '#ffffff')};
            }}
            
            QGroupBox {{
                color: {colors.get('text', '#cccccc')};
                font-weight: bold;
                border: 2px solid {colors.get('mid', '#2d2d30')};
                border-radius: {spacing.get('border_radius', 4)}px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {colors.get('text', '#cccccc')};
                background-color: {colors.get('window', '#1e1e1e')};
            }}
            
            QTableWidget {{
                background-color: {colors.get('base', '#2d2d30')};
                color: {colors.get('text', '#cccccc')};
                gridline-color: {colors.get('mid', '#2d2d30')};
                alternate-background-color: {colors.get('alternate_base', '#252526')};
            }}
            
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {colors.get('mid', '#2d2d30')};
                color: {colors.get('text', '#cccccc')};
            }}
            
            QTableWidget::item:selected {{
                background-color: {colors.get('highlight', '#0078d4')};
                color: {colors.get('highlighted_text', '#ffffff')};
            }}
            
            QHeaderView::section {{
                background-color: {colors.get('button', '#3c3c3c')};
                color: {colors.get('text', '#cccccc')};
                padding: 8px;
                border: 1px solid {colors.get('mid', '#2d2d30')};
                font-weight: bold;
            }}
            
            QScrollBar:vertical {{
                background-color: {colors.get('base', '#2d2d30')};
                width: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {colors.get('mid', '#2d2d30')};
                border-radius: 6px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {colors.get('light', '#4c4c4c')};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QMainWindow {{
                background-color: {colors.get('window', '#1e1e1e')};
                color: {colors.get('text', '#cccccc')};
            }}
            
            QTabWidget {{
                background-color: {colors.get('base', '#2d2d30')};
                color: {colors.get('text', '#cccccc')};
            }}
            
            QCheckBox {{
                color: {colors.get('text', '#cccccc')};
                spacing: 8px;
            }}
            
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {colors.get('mid', '#2d2d30')};
                border-radius: 3px;
                background-color: {colors.get('base', '#2d2d30')};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {colors.get('highlight', '#0078d4')};
                border-color: {colors.get('highlight', '#0078d4')};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {colors.get('highlight', '#0078d4')};
                border-color: {colors.get('highlight', '#0078d4')};
            }}
            
            QRadioButton {{
                color: {colors.get('text', '#cccccc')};
                spacing: 8px;
            }}
            
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {colors.get('mid', '#2d2d30')};
                border-radius: 8px;
                background-color: {colors.get('base', '#2d2d30')};
            }}
            
            QRadioButton::indicator:checked {{
                background-color: {colors.get('highlight', '#0078d4')};
                border-color: {colors.get('highlight', '#0078d4')};
            }}
            
            QRadioButton::indicator:checked {{
                background-color: {colors.get('highlight', '#0078d4')};
                border-color: {colors.get('highlight', '#0078d4')};
            }}
            
            QSpinBox {{
                background-color: {colors.get('base', '#2d2d30')};
                color: {colors.get('text', '#cccccc')};
                border: 2px solid {colors.get('mid', '#2d2d30')};
                border-radius: {spacing.get('border_radius', 4)}px;
                padding: {spacing.get('margin', 4)}px;
                font-size: {fonts.get('base_size', 14)}px;
            }}
            
            QSpinBox:focus {{
                border-color: {colors.get('highlight', '#0078d4')};
            }}
            
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {colors.get('button', '#3c3c3c')};
                border: 1px solid {colors.get('mid', '#2d2d30')};
                border-radius: 2px;
                width: 16px;
            }}
            
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {colors.get('light', '#4c4c4c')};
            }}
            
            QSpinBox::up-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 4px solid {colors.get('text', '#cccccc')};
            }}
            
            QSpinBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {colors.get('text', '#cccccc')};
            }}
            
            QDateEdit {{
                background-color: {colors.get('base', '#2d2d30')};
                color: {colors.get('text', '#cccccc')};
                border: 1px solid {colors.get('light', '#4c4c4c')};
                border-radius: {spacing.get('border_radius', 4)}px;
                padding: {spacing.get('margin', 4)}px;
                font-size: {fonts.get('base_size', 14)}px;
            }}
            
            QDateEdit:hover {{
                border-color: {colors.get('highlight', '#0078d4')};
            }}
            
            QDateEdit:focus {{
                border-color: {colors.get('highlight', '#0078d4')};
                border-width: 2px;
            }}
            
            QDateEdit::drop-down {{
                border: 1px solid {colors.get('light', '#4c4c4c')};
                border-radius: 2px;
                width: 20px;
                background-color: {colors.get('button', '#3c3c3c')};
            }}
            
            QDateEdit::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {colors.get('text', '#cccccc')};
                margin-right: 6px;
            }}
            
            QSpinBox {{
                background-color: {colors.get('base', '#2d2d30')};
                color: {colors.get('text', '#cccccc')};
                border: 1px solid {colors.get('light', '#4c4c4c')};
                border-radius: {spacing.get('border_radius', 4)}px;
                padding: {spacing.get('margin', 4)}px;
                font-size: {fonts.get('base_size', 14)}px;
            }}
            
            QSpinBox:hover {{
                border-color: {colors.get('highlight', '#0078d4')};
            }}
            
            QSpinBox:focus {{
                border-color: {colors.get('highlight', '#0078d4')};
                border-width: 2px;
            }}
            
            QSpinBox::up-button {{
                background-color: {colors.get('button', '#3c3c3c')};
                border: 1px solid {colors.get('light', '#4c4c4c')};
                border-radius: 2px;
                width: 16px;
                height: 12px;
            }}
            
            QSpinBox::up-button:hover {{
                background-color: {colors.get('light', '#4c4c4c')};
                border-color: {colors.get('highlight', '#0078d4')};
            }}
            
            QSpinBox::up-button:pressed {{
                background-color: {colors.get('dark', '#1e1e1e')};
            }}
            
            QSpinBox::up-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 6px solid {colors.get('text', '#cccccc')};
                margin-top: 2px;
            }}
            
            QSpinBox::down-button {{
                background-color: {colors.get('button', '#3c3c3c')};
                border: 1px solid {colors.get('light', '#4c4c4c')};
                border-radius: 2px;
                width: 16px;
                height: 12px;
            }}
            
            QSpinBox::down-button:hover {{
                background-color: {colors.get('light', '#4c4c4c')};
                border-color: {colors.get('highlight', '#0078d4')};
            }}
            
            QSpinBox::down-button:pressed {{
                background-color: {colors.get('dark', '#1e1e1e')};
            }}
            
            QSpinBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {colors.get('text', '#cccccc')};
                margin-top: 2px;
            }}
            
            QToolButton {{
                background-color: {colors.get('button', '#3c3c3c')};
                color: {colors.get('text', '#cccccc')};
                border: 1px solid {colors.get('mid', '#2d2d30')};
                border-radius: {spacing.get('border_radius', 4)}px;
                padding: {spacing.get('padding', 8)}px;
                font-size: {fonts.get('base_size', 14)}px;
            }}
            
            QToolButton:hover {{
                background-color: {colors.get('light', '#4c4c4c')};
                border-color: {colors.get('highlight', '#0078d4')};
            }}
            
            QToolButton:pressed {{
                background-color: {colors.get('dark', '#1e1e1e')};
            }}
            
            QToolButton:disabled {{
                background-color: {colors.get('dark', '#1e1e1e')};
                color: {colors.get('mid', '#2d2d30')};
                border-color: {colors.get('dark', '#1e1e1e')};
            }}
            
            QPushButton[class="danger-button"] {{
                background-color: #e81123;
                color: white;
                border: 1px solid #e81123;
                font-weight: normal;
                outline: none;
                margin: 1px;
                min-height: 20px;
            }}
            
            QPushButton[class="danger-button"]:hover {{
                background-color: #f1707a;
                border-color: #f1707a;
            }}
            
            QPushButton[class="danger-button"]:pressed {{
                background-color: #c50e1f;
                border-color: #c50e1f;
            }}
            
            QPushButton[class="danger-button"]:disabled {{
                background-color: #666666;
                color: #999999;
                border-color: #666666;
            }}
            
            /* Scrollbar styling for dark mode */
            QScrollBar:vertical {{
                background-color: {colors.get('dark', '#1e1e1e')};
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {colors.get('mid', '#2d2d30')};
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {colors.get('light', '#4c4c4c')};
            }}
            
            QScrollBar::handle:vertical:pressed {{
                background-color: {colors.get('highlight', '#0078d4')};
            }}
            
            QScrollBar::add-line:vertical {{
                height: 0px;
                background-color: transparent;
            }}
            
            QScrollBar::sub-line:vertical {{
                height: 0px;
                background-color: transparent;
            }}
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background-color: transparent;
            }}
            
            QScrollBar:horizontal {{
                background-color: {colors.get('dark', '#1e1e1e')};
                height: 12px;
                border-radius: 6px;
                margin: 0px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {colors.get('mid', '#2d2d30')};
                border-radius: 6px;
                min-width: 20px;
                margin: 2px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: {colors.get('light', '#4c4c4c')};
            }}
            
            QScrollBar::handle:horizontal:pressed {{
                background-color: {colors.get('highlight', '#0078d4')};
            }}
            
            QScrollBar::add-line:horizontal {{
                width: 0px;
                background-color: transparent;
            }}
            
            QScrollBar::sub-line:horizontal {{
                width: 0px;
                background-color: transparent;
            }}
            
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background-color: transparent;
            }}
            
            /* Fix selected item background color for better contrast in dark mode */
            QListWidget::item:selected {{
                background-color: #2d2d30;
                border: 2px solid #0078d4;
                border-radius: 4px;
            }}
            
            QListWidget::item:selected:active {{
                background-color: #2d2d30;
                border: 2px solid #0078d4;
                border-radius: 4px;
            }}
            
            QListWidget::item:selected:!active {{
                background-color: #2d2d30;
                border: 2px solid #0078d4;
                border-radius: 4px;
            }}
            """

            app.setStyleSheet(stylesheet)

        except Exception as e:
            print(f"Error applying custom stylesheet: {e}")

    def refresh_data(self):
        """Refresh all data displays."""
        self.refresh_project_list()
        self.populate_project_tag_filter()
        self.refresh_charts()
        self.refresh_tags()

    def refresh_project_list(self):
        """Refresh the project list display."""
        status_filters = self.status_filter.get_selected_items()
        priority_filters = self.priority_filter.get_selected_items()
        tag_filters = self.tag_filter.get_selected_items()
        search_text = self.search_input.text().strip()

        print(f"DEBUG: status_filters = {status_filters}")
        print(f"DEBUG: priority_filters = {priority_filters}")
        print(f"DEBUG: tag_filters = {tag_filters}")

        # Get all projects
        all_projects = self.db_service.get_projects()
        print(f"DEBUG: total projects = {len(all_projects)}")

        # Apply filters
        filtered_projects = all_projects

        # Filter by status (only if specific statuses are selected)
        if status_filters:
            print(f"DEBUG: filtering by status: {status_filters}")
            before_count = len(filtered_projects)
            filtered_projects = [
                p for p in filtered_projects if p.status in status_filters
            ]
            after_count = len(filtered_projects)
            print(f"DEBUG: status filter: {before_count} -> {after_count} projects")

        # Filter by priority (only if specific priorities are selected)
        if priority_filters:
            print(f"DEBUG: filtering by priority: {priority_filters}")
            before_count = len(filtered_projects)
            filtered_projects = [
                p for p in filtered_projects if p.priority in priority_filters
            ]
            after_count = len(filtered_projects)
            print(f"DEBUG: priority filter: {before_count} -> {after_count} projects")

        # Filter by tag (only if specific tags are selected)
        if tag_filters:
            print(f"DEBUG: filtering by tags: {tag_filters}")
            before_count = len(filtered_projects)
            filtered_projects = [
                p
                for p in filtered_projects
                if any(tag["name"] in tag_filters for tag in p.tags)
            ]
            after_count = len(filtered_projects)
            print(f"DEBUG: tag filter: {before_count} -> {after_count} projects")

        # Apply fuzzy search if there's a search query
        if search_text:
            search_fields = ["name", "description"]
            search_results = fuzzy_search(
                search_text, filtered_projects, search_fields, threshold=0.2
            )
            projects = [item for item, score in search_results]
            self.search_results_label.setText(
                f"Showing {len(projects)} of {len(all_projects)} results"
            )
        else:
            projects = filtered_projects
            self.search_results_label.setText(
                f"Showing {len(projects)} of {len(all_projects)} results"
            )

        print(f"DEBUG: final projects count = {len(projects)}")
        print("DEBUG: project statuses =", [p.status for p in projects])
        print("DEBUG: project priorities =", [p.priority for p in projects])

        self.project_list_widget.update_projects(projects, search_text)

    def on_search_text_changed(self):
        """Handle search text changes."""
        self.refresh_project_list()

    def clear_search(self):
        """Clear the search input field."""
        self.search_input.clear()
        self.refresh_project_list()

    def focus_search(self):
        """Focus the search input field."""
        self.search_input.setFocus()

    def refresh_charts(self):
        """Refresh all charts with current data."""
        # Update project chart
        project_times = self.analytics_service.get_time_by_project()
        self.project_chart.plot_time_by_project(project_times)

        # Update productivity chart
        daily_hours = self.analytics_service.get_daily_productivity()
        self.productivity_chart.plot_daily_productivity(daily_hours)

        # Update timer type chart
        timer_stats = self.analytics_service.get_timer_type_stats()
        self.timer_type_chart.plot_timer_types(timer_stats)

        # Update cumulative work chart
        cumulative_data = self.analytics_service.get_cumulative_work_data()
        self.cumulative_work_chart.plot_cumulative_work(cumulative_data)

        # Update tag distribution chart
        tag_distribution = self.analytics_service.get_tag_distribution()
        self.tag_distribution_chart.plot_tag_distribution(tag_distribution)

        # Update project distribution chart
        project_distribution = self.analytics_service.get_project_distribution()
        self.project_distribution_chart.plot_project_distribution(project_distribution)

        # Ensure all charts use the current theme colors
        self.project_chart.update_theme_colors()
        self.productivity_chart.update_theme_colors()
        self.timer_type_chart.update_theme_colors()
        self.cumulative_work_chart.update_theme_colors()
        self.tag_distribution_chart.update_theme_colors()
        self.project_distribution_chart.update_theme_colors()

    def show_previous_chart(self):
        """Show the previous chart in the sequence."""
        if self.current_chart_index > 0:
            self.current_chart_index -= 1
            self.chart_stack.setCurrentIndex(self.current_chart_index)
            self.chart_title_label.setText(self.chart_titles[self.current_chart_index])
            self.update_navigation_buttons()

    def show_next_chart(self):
        """Show the next chart in the sequence."""
        if self.current_chart_index < len(self.chart_titles) - 1:
            self.current_chart_index += 1
            self.chart_stack.setCurrentIndex(self.current_chart_index)
            self.chart_title_label.setText(self.chart_titles[self.current_chart_index])
            self.update_navigation_buttons()

    def update_navigation_buttons(self):
        """Update the state of navigation buttons based on current chart index."""
        self.prev_chart_btn.setEnabled(self.current_chart_index > 0)
        self.next_chart_btn.setEnabled(
            self.current_chart_index < len(self.chart_titles) - 1
        )

    def on_project_selected(self, project: Project):
        """Handle project selection."""
        if self._sync_in_progress:
            return

        self._sync_in_progress = True
        self.current_project_id = project.id

        # Enable task search and filters
        self.task_search_input.setEnabled(True)
        self.clear_task_search_btn.setEnabled(True)
        self.task_status_filter.setEnabled(True)
        self.task_priority_filter.setEnabled(True)
        self.task_tag_filter.setEnabled(True)

        # Populate task tag filter
        self.populate_task_tag_filter(project.id)

        # Clear task search when switching projects
        self.task_search_input.clear()
        self.task_search_results_label.setText("")

        # Refresh task list after everything is set up
        self.refresh_task_list(project.id)

        # Sync with timer tab
        self.timer_widget.set_current_project(project.id)
        self._sync_in_progress = False

    def refresh_task_list(self, project_id: int):
        """Refresh the task list for a selected project."""
        # Check if filters are properly initialized
        if (
            not hasattr(self, "task_status_filter")
            or not hasattr(self, "task_priority_filter")
            or not hasattr(self, "task_tag_filter")
        ):
            return

        status_filters = self.task_status_filter.get_selected_items()
        priority_filters = self.task_priority_filter.get_selected_items()
        tag_filters = self.task_tag_filter.get_selected_items()
        search_text = self.task_search_input.text().strip()

        # Get all tasks for the project
        all_tasks = self.db_service.get_tasks(project_id=project_id)

        # Apply filters
        filtered_tasks = all_tasks

        # Filter by status (only if specific statuses are selected)
        if status_filters:
            status_filtered = []
            for task in filtered_tasks:
                if "completed" in status_filters and task.completed:
                    status_filtered.append(task)
                elif "pending" in status_filters and not task.completed:
                    status_filtered.append(task)
            filtered_tasks = status_filtered

        # Filter by priority (only if specific priorities are selected)
        if priority_filters:
            filtered_tasks = [
                t for t in filtered_tasks if t.priority in priority_filters
            ]

        # Filter by tag (only if specific tags are selected)
        if tag_filters:
            filtered_tasks = [
                t
                for t in filtered_tasks
                if any(tag["name"] in tag_filters for tag in t.tags)
            ]

        # Apply fuzzy search if there's a search query
        if search_text:
            search_fields = ["name", "description"]
            search_results = fuzzy_search(
                search_text, filtered_tasks, search_fields, threshold=0.2
            )
            tasks = [item for item, score in search_results]
            self.task_search_results_label.setText(
                f"Showing {len(tasks)} of {len(all_tasks)} tasks"
            )
        else:
            tasks = filtered_tasks
            self.task_search_results_label.setText(
                f"Showing {len(tasks)} of {len(all_tasks)} tasks"
            )

        self.task_list_widget.update_tasks(tasks, search_text)
        self.add_task_btn.setEnabled(True)

    def on_task_search_text_changed(self):
        """Handle task search text changes."""
        if hasattr(self, "current_project_id") and self.current_project_id:
            self.refresh_task_list(self.current_project_id)

    def on_task_filter_changed(self):
        """Handle task filter changes."""
        if (
            hasattr(self, "current_project_id")
            and self.current_project_id
            and self.current_project_id is not None
        ):
            self.refresh_task_list(self.current_project_id)

    def focus_task_search(self):
        """Focus the task search input field."""
        if hasattr(self, "current_project_id") and self.current_project_id:
            self.task_search_input.setFocus()

    def clear_task_search(self):
        """Clear the task search input field."""
        self.task_search_input.clear()
        if hasattr(self, "current_project_id") and self.current_project_id:
            self.refresh_task_list(self.current_project_id)

    def add_project(self):
        """Add a new project."""
        dialog = ProjectDialog(self)
        if dialog.exec_() == ProjectDialog.Accepted:
            project_data = dialog.get_project_data()

            # Extract tags for separate handling
            tags = project_data.pop("tags", [])

            # Create project
            project = self.db_service.create_project(**project_data)

            # Add tags separately (with cascading to tasks)
            for tag in tags:
                self.db_service.add_project_tag(project.id, tag, cascade_to_tasks=True)

            self.refresh_project_list()
            self.populate_project_tag_filter()  # Update project tag filter

            # Show cascading info if tags were added
            if tags:
                task_count = len(self.db_service.get_tasks(project.id))
                if task_count > 0:
                    self.notification_manager.show_success(
                        "Project Created",
                        f"Project '{project.name}' created successfully! Tags have been automatically applied to all {task_count} tasks in this project.",
                    )
                else:
                    self.notification_manager.show_success(
                        "Project Created",
                        f"Project '{project.name}' created successfully! Tags will be automatically applied to any tasks you add to this project.",
                    )
            else:
                self.notification_manager.show_success(
                    "Project Created", f"Project '{project.name}' created successfully!"
                )

    def edit_project(self, project: Project):
        """Edit an existing project."""
        dialog = ProjectDialog(self, project)
        if dialog.exec_() == ProjectDialog.Accepted:
            if dialog.project is None:
                # Project was deleted
                self.db_service.delete_project(project.id)
                self.refresh_project_list()
                self.populate_project_tag_filter()  # Update project tag filter
                self.notification_manager.show_success(
                    "Project Deleted", f"Project '{project.name}' deleted successfully!"
                )
            else:
                # Project was updated
                project_data = dialog.get_project_data()

                # Extract tags for separate handling
                new_tags = project_data.pop("tags", [])

                # Update project
                updated_project = self.db_service.update_project(
                    project.id, **project_data
                )

                # Update tags (remove old ones, add new ones with cascading)
                for tag in project.tags:
                    # Handle both old string format and new dict format
                    tag_name = tag["name"] if isinstance(tag, dict) else tag
                    self.db_service.remove_project_tag(
                        project.id, tag_name, cascade_to_tasks=True
                    )
                for tag in new_tags:
                    self.db_service.add_project_tag(
                        project.id, tag, cascade_to_tasks=True
                    )

                # Refresh both project list and task list to show updated tags
                self.refresh_project_list()
                if self.current_project_id == project.id:
                    self.refresh_task_list(
                        project.id
                    )  # Refresh task list if this project is currently selected
                    self.populate_task_tag_filter(project.id)  # Update task tag filter
                self.populate_project_tag_filter()  # Update project tag filter
                self.notification_manager.show_success(
                    "Project Updated",
                    f"Project '{updated_project.name}' updated successfully!",
                )

    def delete_project(self, project: Project):
        """Delete a project."""
        reply = QMessageBox.question(
            self,
            "Delete Project",
            f"Are you sure you want to delete project '{project.name}'?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.db_service.delete_project(project.id)
            self.refresh_project_list()
            self.populate_project_tag_filter()  # Update project tag filter
            self.notification_manager.show_success(
                "Project Deleted", f"Project '{project.name}' deleted successfully!"
            )

    def on_timer_started(self, timer: Timer):
        """Handle timer started event."""
        self.refresh_charts()

    def on_timer_stopped(self, timer: Timer):
        """Handle timer stopped event."""
        self.refresh_charts()

    def on_timer_completed(self, timer: Timer):
        """Handle timer completed event."""
        self.refresh_charts()

    def on_timer_project_selected(self, project_id: int):
        """Handle project selection from timer tab."""
        if self._sync_in_progress:
            return

        self._sync_in_progress = True
        if project_id is not None:
            # Find the project and select it in the projects tab
            project = self.db_service.get_project(project_id)
            if project:
                # Update the current project selection in projects tab
                self.current_project_id = project_id

                # Select the project in the project list widget
                self.project_list_widget.set_selected_project(project)

                self.refresh_task_list(project_id)

                # Enable task controls
                self.task_search_input.setEnabled(True)
                self.clear_task_search_btn.setEnabled(True)
                self.task_status_filter.setEnabled(True)
                self.task_priority_filter.setEnabled(True)
                self.task_tag_filter.setEnabled(True)

                # Populate task tag filter
                self.populate_task_tag_filter(project_id)

                # Clear task search
                self.task_search_input.clear()
                self.task_search_results_label.setText("")
        else:
            # Clear project selection
            self.current_project_id = None
            self.task_search_input.setEnabled(False)
            self.clear_task_search_btn.setEnabled(False)
            self.task_status_filter.setEnabled(False)
            self.task_priority_filter.setEnabled(False)
            self.task_tag_filter.setEnabled(False)
            self.add_task_btn.setEnabled(False)

            # Clear task list
            self.task_list_widget.clear()
            self.task_search_results_label.setText("")
        self._sync_in_progress = False

    def on_timer_task_selected(self, task: Task):
        """Handle task selection from timer tab."""
        if self._sync_in_progress:
            return

        self._sync_in_progress = True
        if task is not None:
            # First ensure the project is selected in the projects tab
            if self.current_project_id != task.project_id:
                # Find and select the project
                project = self.db_service.get_project(task.project_id)
                if project:
                    self.current_project_id = task.project_id
                    self.refresh_task_list(task.project_id)

                    # Enable task controls
                    self.task_search_input.setEnabled(True)
                    self.clear_task_search_btn.setEnabled(True)
                    self.task_status_filter.setEnabled(True)
                    self.task_priority_filter.setEnabled(True)
                    self.task_tag_filter.setEnabled(True)

                    # Populate task tag filter
                    self.populate_task_tag_filter(task.project_id)

                    # Clear task search
                    self.task_search_input.clear()
                    self.task_search_results_label.setText("")

            # Then update the task selection in projects tab
            self.task_list_widget.set_selected_task(task)
        self._sync_in_progress = False

    def start_timer(self):
        """Start a timer for the first available task."""
        tasks = self.db_service.get_tasks()
        if tasks:
            # Start timer for the first task (in a real app, you'd let user select)
            timer = self.timer_controller.start_timer(tasks[0].id, "stopwatch")
            self.refresh_charts()

    def stop_timer(self):
        """Stop the current timer."""
        timer = self.timer_controller.stop_timer()
        if timer:
            self.refresh_charts()

    def add_task(self):
        """Add a new task."""
        if not hasattr(self, "current_project_id") or self.current_project_id is None:
            QMessageBox.warning(
                self, "No Project Selected", "Please select a project first."
            )
            return

        dialog = TaskDialog(self, project_id=self.current_project_id)
        if dialog.exec_() == TaskDialog.Accepted:
            task_data = dialog.get_task_data()

            # Extract tags for separate handling
            tags = task_data.pop("tags", [])

            # Create task
            task = self.db_service.create_task(**task_data)

            # Add tags separately (with cascading to project)
            for tag in tags:
                self.db_service.add_task_tag(task.id, tag, cascade_to_project=True)

            # Refresh both task list and project list to show updated tags
            self.refresh_task_list(self.current_project_id)
            self.refresh_project_list()  # Refresh project list to show updated project tags
            self.populate_task_tag_filter(
                self.current_project_id
            )  # Update task tag filter
            self.populate_project_tag_filter()  # Update project tag filter

            # Show cascading info if tags were added
            if tags:
                self.notification_manager.show_success(
                    "Task Created",
                    f"Task '{task.name}' created successfully! Tags have been automatically added to the project as well.",
                )
            else:
                self.notification_manager.show_success(
                    "Task Created", f"Task '{task.name}' created successfully!"
                )

    def edit_task(self, task: Task):
        """Edit an existing task."""
        dialog = TaskDialog(self, task=task)
        if dialog.exec_() == TaskDialog.Accepted:
            if dialog.task is None:
                # Task was deleted
                self.db_service.delete_task(task.id)
                self.refresh_task_list(self.current_project_id)
                self.notification_manager.show_success(
                    "Task Deleted", f"Task '{task.name}' deleted successfully!"
                )
            else:
                # Task was updated
                task_data = dialog.get_task_data()

                # Extract tags for separate handling
                new_tags = task_data.pop("tags", [])

                # Update task
                updated_task = self.db_service.update_task(task.id, **task_data)

                # Update tags (remove old ones, add new ones with cascading)
                for tag in task.tags:
                    # Handle both old string format and new dict format
                    tag_name = tag["name"] if isinstance(tag, dict) else tag
                    self.db_service.remove_task_tag(
                        task.id, tag_name, cascade_to_project=True
                    )
                for tag in new_tags:
                    self.db_service.add_task_tag(task.id, tag, cascade_to_project=True)

                # Refresh both task list and project list to show updated tags
                self.refresh_task_list(self.current_project_id)
                self.refresh_project_list()  # Refresh project list to show updated project tags
                self.populate_task_tag_filter(
                    self.current_project_id
                )  # Update task tag filter
                self.populate_project_tag_filter()  # Update project tag filter

                self.notification_manager.show_success(
                    "Task Updated", f"Task '{updated_task.name}' updated successfully!"
                )

    def delete_task(self, task: Task):
        """Delete a task."""
        reply = QMessageBox.question(
            self,
            "Delete Task",
            f"Are you sure you want to delete task '{task.name}'?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.db_service.delete_task(task.id)
            # Refresh both task list and project list (deleting task might affect project tags)
            self.refresh_task_list(self.current_project_id)
            self.refresh_project_list()
            self.populate_task_tag_filter(
                self.current_project_id
            )  # Update task tag filter
            self.populate_project_tag_filter()  # Update project tag filter
            self.notification_manager.show_success(
                "Task Deleted", f"Task '{task.name}' deleted successfully!"
            )

    def on_task_selected(self, task: Task):
        """Handle task selection."""
        if self._sync_in_progress:
            return

        self._sync_in_progress = True
        # Set the selected task in the timer widget
        if hasattr(self, "timer_widget") and task is not None:
            # Make sure the project is also selected in timer tab
            if hasattr(self, "current_project_id") and self.current_project_id:
                self.timer_widget.set_current_project_and_task(
                    self.current_project_id, task
                )
            else:
                self.timer_widget.set_current_task(task)
        self._sync_in_progress = False

    def add_sample_task(self):
        """Add a sample task for testing."""
        from datetime import datetime, timedelta

        projects = self.db_service.get_projects()
        if projects:
            task = self.db_service.create_task(
                project_id=projects[0].id,
                name=f"Sample Task {datetime.now().strftime('%H:%M')}",
                due_date=datetime.now() + timedelta(days=7),
            )
            self.refresh_task_list(projects[0].id)

    def refresh_tags(self):
        """Refresh the list of tags."""
        search_text = self.tag_search_input.text().strip()
        sort_option = self.tag_sort_combo.currentText()

        all_tags = self.db_service.get_tags()

        # Apply search filter
        if search_text:
            search_fields = ["name"]
            search_results = fuzzy_search(
                search_text, all_tags, search_fields, threshold=0.2
            )
            tags = [item for item, score in search_results]
        else:
            tags = all_tags

        # Apply sorting
        if sort_option == "Name (A-Z)":
            tags.sort(key=lambda x: x.name.lower())
        elif sort_option == "Name (Z-A)":
            tags.sort(key=lambda x: x.name.lower(), reverse=True)
        elif sort_option == "Popularity (High-Low)":
            tags.sort(key=lambda x: x.usage_count, reverse=True)
        elif sort_option == "Popularity (Low-High)":
            tags.sort(key=lambda x: x.usage_count)

        self.tag_search_results_label.setText(
            f"Showing {len(tags)} of {len(all_tags)} tags"
        )

        self.tag_list_widget.update_tags(tags, search_text)

    def on_tag_search_text_changed(self):
        """Handle tag search text changes."""
        self.refresh_tags()

    def on_tag_sort_changed(self):
        """Handle tag sort option changes."""
        self.refresh_tags()

    def focus_tag_search(self):
        """Focus the tag search input field."""
        self.tag_search_input.setFocus()

    def clear_tag_search(self):
        """Clear the tag search input field."""
        self.tag_search_input.clear()
        self.refresh_tags()

    def on_tag_selected(self, tag: Tag):
        """Handle tag selection."""
        # This method is not strictly needed for the current implementation
        # as the tag_list_widget handles selection internally.
        # However, it can be used if specific actions are needed on tag selection.
        pass

    def edit_tag(self, tag: Tag):
        """Edit the tag."""
        dialog = TagDialog(tag.name, tag.color, tag.description, parent=self)
        if dialog.exec() == QDialog.Accepted:
            tag_data = dialog.get_tag_data()
            if tag_data["name"]:
                if self.db_service.update_tag(
                    tag.name,
                    tag_data["name"],
                    tag_data["color"],
                    tag_data["description"],
                ):
                    # Refresh all UI components that display tags
                    self.refresh_tags()
                    self.refresh_project_list()
                    if hasattr(self, "current_project_id") and self.current_project_id:
                        self.refresh_task_list(self.current_project_id)
                        self.populate_task_tag_filter(self.current_project_id)
                    self.populate_project_tag_filter()
                    self.notification_manager.show_success(
                        "Tag Updated",
                        f"Tag '{tag.name}' updated to '{tag_data['name']}'",
                    )
                else:
                    self.notification_manager.show_error(
                        "Update Failed",
                        f"Tag '{tag_data['name']}' already exists or could not be updated.",
                    )

    def delete_tag(self, tag: Tag):
        """Delete a tag."""
        if self.db_service.delete_tag(tag.name):
            # Refresh all UI components that display tags
            self.refresh_tags()
            self.refresh_project_list()
            if hasattr(self, "current_project_id") and self.current_project_id:
                self.refresh_task_list(self.current_project_id)
                self.populate_task_tag_filter(self.current_project_id)
            self.populate_project_tag_filter()
            self.notification_manager.show_success(
                "Tag Deleted", f"Tag '{tag.name}' deleted successfully!"
            )
        else:
            self.notification_manager.show_error(
                "Delete Failed", f"Tag '{tag.name}' could not be deleted."
            )

    def add_tag(self):
        """Add a new tag."""
        dialog = TagDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            tag_data = dialog.get_tag_data()
            if tag_data["name"]:
                if self.db_service.add_tag(
                    tag_data["name"], tag_data["color"], tag_data["description"]
                ):
                    # Refresh all UI components that display tags
                    self.refresh_tags()
                    self.refresh_project_list()
                    if hasattr(self, "current_project_id") and self.current_project_id:
                        self.refresh_task_list(self.current_project_id)
                        self.populate_task_tag_filter(self.current_project_id)
                    self.populate_project_tag_filter()
                    self.notification_manager.show_success(
                        "Tag Added", f"Tag '{tag_data['name']}' added successfully!"
                    )
                else:
                    self.notification_manager.show_error(
                        "Add Failed", f"Tag '{tag_data['name']}' already exists."
                    )

    def populate_project_tag_filter(self):
        """Populate the project tag filter with all available tags."""
        # Get all available tags from database
        all_tags = self.db_service.get_all_tags()

        # Set tags to filter
        self.tag_filter.set_items(sorted(all_tags))

    def populate_task_tag_filter(self, project_id: int):
        """Populate the task tag filter with all available tags."""
        # Get all available tags from database
        all_tags = self.db_service.get_all_tags()

        # Set tags to filter
        self.task_tag_filter.set_items(sorted(all_tags))

    def clear_all_data(self):
        """Clear all data from the database."""
        from app.services.data_init import DataInitializer

        initializer = DataInitializer(self.db_service)
        initializer.clear_all_data()
        self.refresh_data()

    def reset_to_sample_data(self):
        """Reset database to sample data."""
        from app.services.data_init import DataInitializer

        initializer = DataInitializer(self.db_service)
        initializer.clear_all_data()
        initializer.initialize_sample_data()
        self.refresh_data()

    def get_all_project_statuses(self) -> List[str]:
        """Get all possible project statuses from database and hardcoded values."""
        # Get all statuses currently used in projects
        all_projects = self.db_service.get_projects()
        used_statuses = set()
        for project in all_projects:
            if project.status:
                used_statuses.add(project.status)

        # Add hardcoded possible values
        all_possible_statuses = {"active", "paused", "completed", "cancelled"}

        # Combine and return sorted list
        return sorted(list(used_statuses.union(all_possible_statuses)))

    def get_all_project_priorities(self) -> List[str]:
        """Get all possible project priorities from database and hardcoded values."""
        # Get all priorities currently used in projects
        all_projects = self.db_service.get_projects()
        used_priorities = set()
        for project in all_projects:
            if project.priority:
                used_priorities.add(project.priority)

        # Add hardcoded possible values
        all_possible_priorities = {"low", "medium", "high", "urgent"}

        # Combine and return sorted list
        return sorted(list(used_priorities.union(all_possible_priorities)))

    def get_all_task_statuses(self) -> List[str]:
        """Get all possible task statuses from database and hardcoded values."""
        # Get all statuses currently used in tasks
        all_tasks = self.db_service.get_tasks()
        used_statuses = set()
        for task in all_tasks:
            status = "completed" if task.completed else "pending"
            used_statuses.add(status)

        # Add hardcoded possible values
        all_possible_statuses = {"pending", "completed"}

        # Combine and return sorted list
        return sorted(list(used_statuses.union(all_possible_statuses)))

    def get_all_task_priorities(self) -> List[str]:
        """Get all possible task priorities from database and hardcoded values."""
        # Get all priorities currently used in tasks
        all_tasks = self.db_service.get_tasks()
        used_priorities = set()
        for task in all_tasks:
            if task.priority:
                used_priorities.add(task.priority)

        # Add hardcoded possible values
        all_possible_priorities = {"low", "medium", "high", "urgent"}

        # Combine and return sorted list
        return sorted(list(used_priorities.union(all_possible_priorities)))
