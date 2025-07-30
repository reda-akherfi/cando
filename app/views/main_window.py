"""
Main window view for the Cando application.

This module contains the main window class that manages the application's
primary user interface with tabbed views for different functionality.
"""

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
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QShortcut, QKeySequence
from app.ui.chart_widget import (
    TimeByProjectChart,
    DailyProductivityChart,
    TimerTypeChart,
)
from app.ui.theme import DarkTheme, LightTheme
from app.ui.project_dialog import ProjectDialog
from app.ui.project_list_widget import ProjectListWidget
from app.ui.task_dialog import TaskDialog
from app.ui.task_list_widget import TaskListWidget
from app.ui.tag_dialog import TagDialog
from app.ui.tag_list_widget import TagListWidget
from app.ui.timer_widget import TimerWidget
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
        self.setup_tabs()
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

        # Create refresh button
        refresh_button = QPushButton("Refresh Charts")
        refresh_button.clicked.connect(self.refresh_charts)

        # Add widgets to layout
        layout.addWidget(QLabel("Time by Project"))
        layout.addWidget(self.project_chart)
        layout.addWidget(QLabel("Daily Productivity"))
        layout.addWidget(self.productivity_chart)
        layout.addWidget(QLabel("Timer Type Usage"))
        layout.addWidget(self.timer_type_chart)
        layout.addWidget(refresh_button)

    def setup_projects_tab(self):
        """Set up the projects tab for project and task management."""
        layout = QVBoxLayout(self.projects_tab)

        # Project management controls
        controls_layout = QHBoxLayout()

        # Search functionality
        search_label = QLabel("Search:")
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
        self.clear_search_btn.setMaximumWidth(60)

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.clear_search_btn)

        controls_layout.addWidget(search_label)
        controls_layout.addLayout(search_layout)

        # Filter controls
        # Status filter
        status_label = QLabel("Status:")
        self.status_filter = QComboBox()
        self.status_filter.addItems(
            ["All", "active", "paused", "completed", "cancelled"]
        )
        self.status_filter.currentTextChanged.connect(self.refresh_project_list)
        self.status_filter.setMaximumWidth(100)

        # Priority filter
        priority_label = QLabel("Priority:")
        self.priority_filter = QComboBox()
        self.priority_filter.addItems(["All", "low", "medium", "high"])
        self.priority_filter.currentTextChanged.connect(self.refresh_project_list)
        self.priority_filter.setMaximumWidth(100)

        # Tag filter
        tag_label = QLabel("Tag:")
        self.tag_filter = QComboBox()
        self.tag_filter.addItem("All")
        self.tag_filter.currentTextChanged.connect(self.refresh_project_list)
        self.tag_filter.setMaximumWidth(120)

        controls_layout.addWidget(status_label)
        controls_layout.addWidget(self.status_filter)
        controls_layout.addWidget(priority_label)
        controls_layout.addWidget(self.priority_filter)
        controls_layout.addWidget(tag_label)
        controls_layout.addWidget(self.tag_filter)
        controls_layout.addStretch()

        # Action buttons
        self.add_project_btn = QPushButton("+")
        self.add_project_btn.clicked.connect(self.add_project)
        self.add_project_btn.setMaximumWidth(40)
        self.add_project_btn.setToolTip("Add Project")

        controls_layout.addWidget(self.add_project_btn)

        layout.addLayout(controls_layout)

        # Search results counter
        self.search_results_label = QLabel("")
        self.search_results_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.search_results_label)

        # Project list
        self.project_list_widget = ProjectListWidget()
        self.project_list_widget.project_edit_requested.connect(self.edit_project)
        self.project_list_widget.project_delete_requested.connect(self.delete_project)
        self.project_list_widget.project_selected.connect(self.on_project_selected)

        layout.addWidget(self.project_list_widget)

        # Task management section
        task_section_label = QLabel("Tasks:")
        task_section_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(task_section_label)

        # Task search and filter functionality
        task_controls_layout = QHBoxLayout()

        # Task search
        task_search_label = QLabel("Search Tasks:")
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
        self.clear_task_search_btn.setMaximumWidth(60)
        self.clear_task_search_btn.setEnabled(
            False
        )  # Disabled until project is selected

        task_search_layout = QHBoxLayout()
        task_search_layout.addWidget(self.task_search_input)
        task_search_layout.addWidget(self.clear_task_search_btn)

        task_controls_layout.addWidget(task_search_label)
        task_controls_layout.addLayout(task_search_layout)

        # Task filters
        # Task status filter
        task_status_label = QLabel("Status:")
        self.task_status_filter = QComboBox()
        self.task_status_filter.addItems(["All", "pending", "completed"])
        self.task_status_filter.currentTextChanged.connect(self.on_task_filter_changed)
        self.task_status_filter.setMaximumWidth(100)
        self.task_status_filter.setEnabled(False)  # Disabled until project is selected

        # Task priority filter
        task_priority_label = QLabel("Priority:")
        self.task_priority_filter = QComboBox()
        self.task_priority_filter.addItems(["All", "low", "medium", "high"])
        self.task_priority_filter.currentTextChanged.connect(
            self.on_task_filter_changed
        )
        self.task_priority_filter.setMaximumWidth(100)
        self.task_priority_filter.setEnabled(
            False
        )  # Disabled until project is selected

        # Task tag filter
        task_tag_label = QLabel("Tag:")
        self.task_tag_filter = QComboBox()
        self.task_tag_filter.addItem("All")
        self.task_tag_filter.currentTextChanged.connect(self.on_task_filter_changed)
        self.task_tag_filter.setMaximumWidth(120)
        self.task_tag_filter.setEnabled(False)  # Disabled until project is selected

        task_controls_layout.addWidget(task_status_label)
        task_controls_layout.addWidget(self.task_status_filter)
        task_controls_layout.addWidget(task_priority_label)
        task_controls_layout.addWidget(self.task_priority_filter)
        task_controls_layout.addWidget(task_tag_label)
        task_controls_layout.addWidget(self.task_tag_filter)
        task_controls_layout.addStretch()

        # Add task button
        self.add_task_btn = QPushButton("+")
        self.add_task_btn.clicked.connect(self.add_task)
        self.add_task_btn.setMaximumWidth(40)
        self.add_task_btn.setToolTip("Add Task")
        self.add_task_btn.setEnabled(False)  # Disabled until project is selected

        task_controls_layout.addWidget(self.add_task_btn)

        layout.addLayout(task_controls_layout)

        # Task search results counter
        self.task_search_results_label = QLabel("")
        self.task_search_results_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.task_search_results_label)

        # Task list
        self.task_list_widget = TaskListWidget()
        self.task_list_widget.task_edit_requested.connect(self.edit_task)
        self.task_list_widget.task_delete_requested.connect(self.delete_task)
        self.task_list_widget.task_selected.connect(self.on_task_selected)

        layout.addWidget(self.task_list_widget)

    def setup_timer_tab(self):
        """Set up the timer tab with comprehensive timer widget."""
        layout = QVBoxLayout(self.timer_tab)

        # Create scroll area for the timer widget
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Create and add the comprehensive timer widget
        self.timer_widget = TimerWidget(self.timer_controller, self.db_service)
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

        # Add theme toggle
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        self.theme_button = QPushButton("Switch to Light Mode")
        self.theme_button.clicked.connect(self.toggle_theme)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_button)
        theme_layout.addStretch()

        # Add window behavior settings
        window_layout = QHBoxLayout()
        window_label = QLabel("Always open in maximized mode:")
        self.maximized_checkbox = QCheckBox()
        self.maximized_checkbox.setChecked(
            self.db_service.get_config("always_maximized", "true").lower() == "true"
        )
        self.maximized_checkbox.toggled.connect(self.on_maximized_setting_changed)
        window_layout.addWidget(window_label)
        window_layout.addWidget(self.maximized_checkbox)
        window_layout.addStretch()

        # Add settings controls
        clear_data_btn = QPushButton("Clear All Data")
        clear_data_btn.clicked.connect(self.clear_all_data)

        reset_data_btn = QPushButton("Reset to Sample Data")
        reset_data_btn.clicked.connect(self.reset_to_sample_data)

        # Add widgets to layout
        layout.addWidget(QLabel("Appearance"))
        layout.addLayout(theme_layout)
        layout.addWidget(QLabel("Window Behavior"))
        layout.addLayout(window_layout)
        layout.addWidget(QLabel("Database Settings"))
        layout.addWidget(clear_data_btn)
        layout.addWidget(reset_data_btn)
        layout.addStretch()

    def setup_tags_tab(self):
        """Set up the tags tab for managing tags."""
        layout = QVBoxLayout(self.tags_tab)

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
        self.clear_tag_search_btn.setMaximumWidth(60)

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

        layout.addLayout(controls_layout)

        # Tag search results counter
        self.tag_search_results_label = QLabel("")
        self.tag_search_results_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.tag_search_results_label)

        # Tag list
        self.tag_list_widget = TagListWidget()
        self.tag_list_widget.tag_edit_requested.connect(self.edit_tag)
        self.tag_list_widget.tag_delete_requested.connect(self.delete_tag)
        self.tag_list_widget.tag_selected.connect(self.on_tag_selected)
        layout.addWidget(self.tag_list_widget)

        # Add new tag button
        self.add_tag_btn = QPushButton("Add Tag")
        self.add_tag_btn.clicked.connect(self.add_tag)
        layout.addWidget(self.add_tag_btn)

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

    def refresh_data(self):
        """Refresh all data displays."""
        self.refresh_project_list()
        self.populate_project_tag_filter()
        self.refresh_charts()
        self.refresh_tags()

    def refresh_project_list(self):
        """Refresh the project list display."""
        status_filter = self.status_filter.currentText()
        priority_filter = self.priority_filter.currentText()
        tag_filter = self.tag_filter.currentText()
        search_text = self.search_input.text().strip()

        # Get all projects
        all_projects = self.db_service.get_projects()

        # Apply filters
        filtered_projects = all_projects

        # Filter by status
        if status_filter != "All":
            filtered_projects = [
                p for p in filtered_projects if p.status == status_filter
            ]

        # Filter by priority
        if priority_filter != "All":
            filtered_projects = [
                p for p in filtered_projects if p.priority == priority_filter
            ]

        # Filter by tag
        if tag_filter != "All":
            filtered_projects = [
                p
                for p in filtered_projects
                if any(tag["name"] == tag_filter for tag in p.tags)
            ]

        # Apply fuzzy search if there's a search query
        if search_text:
            search_fields = ["name", "description"]
            search_results = fuzzy_search(
                search_text, filtered_projects, search_fields, threshold=0.2
            )
            projects = [item for item, score in search_results]
            self.search_results_label.setText(
                f"Showing {len(projects)} of {len(filtered_projects)} results"
            )
        else:
            projects = filtered_projects
            self.search_results_label.setText(
                f"Showing {len(projects)} of {len(filtered_projects)} results"
            )

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

        status_filter = self.task_status_filter.currentText()
        priority_filter = self.task_priority_filter.currentText()
        tag_filter = self.task_tag_filter.currentText()
        search_text = self.task_search_input.text().strip()

        # Get all tasks for the project
        all_tasks = self.db_service.get_tasks(project_id=project_id)

        # Apply filters
        filtered_tasks = all_tasks

        # Filter by status
        if status_filter != "All":
            if status_filter == "completed":
                filtered_tasks = [t for t in filtered_tasks if t.completed]
            elif status_filter == "pending":
                filtered_tasks = [t for t in filtered_tasks if not t.completed]

        # Filter by priority
        if priority_filter != "All":
            filtered_tasks = [
                t for t in filtered_tasks if t.priority == priority_filter
            ]

        # Filter by tag
        if tag_filter != "All":
            filtered_tasks = [
                t
                for t in filtered_tasks
                if any(tag["name"] == tag_filter for tag in t.tags)
            ]

        # Apply fuzzy search if there's a search query
        if search_text:
            search_fields = ["name", "description"]
            search_results = fuzzy_search(
                search_text, filtered_tasks, search_fields, threshold=0.2
            )
            tasks = [item for item, score in search_results]
            self.task_search_results_label.setText(
                f"Showing {len(tasks)} of {len(filtered_tasks)} tasks"
            )
        else:
            tasks = filtered_tasks
            self.task_search_results_label.setText(
                f"Showing {len(tasks)} of {len(filtered_tasks)} tasks"
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
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Project '{project.name}' created successfully!\n\n"
                        f"Tags have been automatically applied to all {task_count} tasks in this project.",
                    )
                else:
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Project '{project.name}' created successfully!\n\n"
                        "Tags will be automatically applied to any tasks you add to this project.",
                    )
            else:
                QMessageBox.information(
                    self, "Success", f"Project '{project.name}' created successfully!"
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
                QMessageBox.information(
                    self, "Success", f"Project '{project.name}' deleted successfully!"
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
                QMessageBox.information(
                    self,
                    "Success",
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
            QMessageBox.information(
                self, "Success", f"Project '{project.name}' deleted successfully!"
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
                QMessageBox.information(
                    self,
                    "Success",
                    f"Task '{task.name}' created successfully!\n\n"
                    "Tags have been automatically added to the project as well.",
                )
            else:
                QMessageBox.information(
                    self, "Success", f"Task '{task.name}' created successfully!"
                )

    def edit_task(self, task: Task):
        """Edit an existing task."""
        dialog = TaskDialog(self, task=task)
        if dialog.exec_() == TaskDialog.Accepted:
            if dialog.task is None:
                # Task was deleted
                self.db_service.delete_task(task.id)
                self.refresh_task_list(self.current_project_id)
                QMessageBox.information(
                    self, "Success", f"Task '{task.name}' deleted successfully!"
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

                QMessageBox.information(
                    self,
                    "Success",
                    f"Task '{updated_task.name}' updated successfully!",
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
            QMessageBox.information(
                self, "Success", f"Task '{task.name}' deleted successfully!"
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
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Tag '{tag.name}' updated to '{tag_data['name']}'",
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Error",
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
            QMessageBox.information(
                self, "Success", f"Tag '{tag.name}' deleted successfully!"
            )
        else:
            QMessageBox.warning(
                self, "Error", f"Tag '{tag.name}' could not be deleted."
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
                    QMessageBox.information(
                        self, "Success", f"Tag '{tag_data['name']}' added successfully!"
                    )
                else:
                    QMessageBox.warning(
                        self, "Error", f"Tag '{tag_data['name']}' already exists."
                    )

    def populate_project_tag_filter(self):
        """Populate the project tag filter with all available tags."""
        self.tag_filter.clear()
        self.tag_filter.addItem("All")

        # Get all unique tags from projects
        all_projects = self.db_service.get_projects()
        all_tags = set()
        for project in all_projects:
            if project.tags:
                all_tags.update([tag["name"] for tag in project.tags])

        # Add tags to filter
        for tag in sorted(all_tags):
            self.tag_filter.addItem(tag)

    def populate_task_tag_filter(self, project_id: int):
        """Populate the task tag filter with tags from the selected project's tasks."""
        self.task_tag_filter.clear()
        self.task_tag_filter.addItem("All")

        # Get all unique tags from tasks in the project
        all_tasks = self.db_service.get_tasks(project_id=project_id)
        all_tags = set()
        for task in all_tasks:
            if task.tags:
                all_tags.update([tag["name"] for tag in task.tags])

        # Add tags to filter
        for tag in sorted(all_tags):
            self.task_tag_filter.addItem(tag)

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
