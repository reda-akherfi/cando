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
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from app.ui.chart_widget import (
    TimeByProjectChart,
    DailyProductivityChart,
    TimerTypeChart,
)
from app.ui.theme import DarkTheme
from app.ui.project_dialog import ProjectDialog
from app.ui.project_list_widget import ProjectListWidget
from app.ui.task_dialog import TaskDialog
from app.ui.task_list_widget import TaskListWidget
from app.ui.ui_main import UiMainWindow
from app.models.project import Project
from app.models.task import Task
from app.services.database import DatabaseService
from app.services.analytics import AnalyticsService
from app.controllers.timer_controller import TimerController
from app.utils.fuzzy_search import fuzzy_search


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
        self.timer_tab = QWidget()
        self.settings_tab = QWidget()

        # Add tabs
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        self.tab_widget.addTab(self.projects_tab, "Projects")
        self.tab_widget.addTab(self.timer_tab, "Timer")
        self.tab_widget.addTab(self.settings_tab, "Settings")

        # Set up tab layouts
        self.setup_dashboard_tab()
        self.setup_projects_tab()
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
        self.search_input.setMinimumWidth(300)

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
        filter_label = QLabel("Filter by Status:")
        self.status_filter = QComboBox()
        self.status_filter.addItems(
            ["All", "active", "paused", "completed", "cancelled"]
        )
        self.status_filter.currentTextChanged.connect(self.refresh_project_list)

        controls_layout.addWidget(filter_label)
        controls_layout.addWidget(self.status_filter)
        controls_layout.addStretch()

        # Action buttons
        self.add_project_btn = QPushButton("Add Project")
        self.add_project_btn.clicked.connect(self.add_project)

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

        # Task controls
        task_controls_layout = QHBoxLayout()
        self.add_task_btn = QPushButton("Add Task")
        self.add_task_btn.clicked.connect(self.add_task)
        self.add_task_btn.setEnabled(False)  # Disabled until project is selected

        task_controls_layout.addWidget(self.add_task_btn)
        task_controls_layout.addStretch()

        layout.addLayout(task_controls_layout)

        # Task list
        self.task_list_widget = TaskListWidget()
        self.task_list_widget.task_edit_requested.connect(self.edit_task)
        self.task_list_widget.task_delete_requested.connect(self.delete_task)
        self.task_list_widget.task_selected.connect(self.on_task_selected)

        layout.addWidget(self.task_list_widget)

    def setup_timer_tab(self):
        """Set up the timer tab with timer controls."""
        layout = QVBoxLayout(self.timer_tab)

        # Add timer controls
        layout.addWidget(self.ui.start_button)
        layout.addWidget(self.ui.stop_button)

        # Connect buttons to timer controller
        self.ui.start_button.clicked.connect(self.start_timer)
        self.ui.stop_button.clicked.connect(self.stop_timer)

        # Add timer status label
        self.timer_status_label = QLabel("No active timer")
        layout.addWidget(self.timer_status_label)

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

        # Add settings controls
        clear_data_btn = QPushButton("Clear All Data")
        clear_data_btn.clicked.connect(self.clear_all_data)

        reset_data_btn = QPushButton("Reset to Sample Data")
        reset_data_btn.clicked.connect(self.reset_to_sample_data)

        # Add widgets to layout
        layout.addWidget(QLabel("Appearance"))
        layout.addLayout(theme_layout)
        layout.addWidget(QLabel("Database Settings"))
        layout.addWidget(clear_data_btn)
        layout.addWidget(reset_data_btn)
        layout.addStretch()

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        app = QApplication.instance()

        if self.is_dark_theme:
            # Switch to light theme (reset to default)
            app.setPalette(app.style().standardPalette())
            app.setStyleSheet("")
            self.theme_button.setText("Switch to Dark Mode")
            self.is_dark_theme = False
        else:
            # Switch to dark theme
            DarkTheme.apply_to_application(app)
            self.theme_button.setText("Switch to Light Mode")
            self.is_dark_theme = True

        # Refresh charts to update their appearance
        self.refresh_charts()

    def refresh_data(self):
        """Refresh all data displays."""
        self.refresh_project_list()
        self.refresh_charts()

    def refresh_project_list(self):
        """Refresh the project list display."""
        status_filter = self.status_filter.currentText()
        search_text = self.search_input.text().strip()

        # Get all projects or filter by status
        if status_filter == "All":
            all_projects = self.db_service.get_projects()
        else:
            all_projects = self.db_service.get_projects(status=status_filter)

        # Apply fuzzy search if there's a search query
        if search_text:
            search_fields = ["name", "description"]
            search_results = fuzzy_search(
                search_text, all_projects, search_fields, threshold=0.2
            )
            projects = [item for item, score in search_results]
            self.search_results_label.setText(
                f"Showing {len(projects)} of {len(all_projects)} results"
            )
        else:
            projects = all_projects
            self.search_results_label.setText(
                f"Showing {len(projects)} of {len(all_projects)} results"
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
        self.current_project_id = project.id
        self.refresh_task_list(project.id)

    def refresh_task_list(self, project_id: int):
        """Refresh the task list for a selected project."""
        tasks = self.db_service.get_tasks(project_id=project_id)
        self.task_list_widget.update_tasks(tasks)
        self.add_task_btn.setEnabled(True)

    def add_project(self):
        """Add a new project."""
        dialog = ProjectDialog(self)
        if dialog.exec_() == ProjectDialog.Accepted:
            project_data = dialog.get_project_data()

            # Extract tags for separate handling
            tags = project_data.pop("tags", [])

            # Create project
            project = self.db_service.create_project(**project_data)

            # Add tags separately
            for tag in tags:
                self.db_service.add_project_tag(project.id, tag)

            self.refresh_project_list()
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

                # Update tags (remove old ones, add new ones)
                # This is a simplified approach - in a real app you'd want to be more efficient
                for tag in project.tags:
                    self.db_service.remove_project_tag(project.id, tag)
                for tag in new_tags:
                    self.db_service.add_project_tag(project.id, tag)

                self.refresh_project_list()
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
            QMessageBox.information(
                self, "Success", f"Project '{project.name}' deleted successfully!"
            )

    def start_timer(self):
        """Start a timer for the first available task."""
        tasks = self.db_service.get_tasks()
        if tasks:
            # Start timer for the first task (in a real app, you'd let user select)
            timer = self.timer_controller.start_timer(tasks[0].id, "stopwatch")
            self.timer_status_label.setText(f"Timer started for: {tasks[0].name}")
            self.refresh_charts()

    def stop_timer(self):
        """Stop the current timer."""
        timer = self.timer_controller.stop_timer()
        if timer:
            self.timer_status_label.setText("Timer stopped")
            self.refresh_charts()
        else:
            self.timer_status_label.setText("No active timer to stop")

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

            # Add tags separately
            for tag in tags:
                self.db_service.add_task_tag(task.id, tag)

            self.refresh_task_list(self.current_project_id)
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

                # Update tags (remove old ones, add new ones)
                for tag in task.tags:
                    self.db_service.remove_task_tag(task.id, tag)
                for tag in new_tags:
                    self.db_service.add_task_tag(task.id, tag)

                self.refresh_task_list(self.current_project_id)
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
            self.refresh_task_list(self.current_project_id)
            QMessageBox.information(
                self, "Success", f"Task '{task.name}' deleted successfully!"
            )

    def on_task_selected(self, task: Task):
        """Handle task selection."""
        # This method is not strictly needed for the current implementation
        # as the task_list_widget handles selection internally.
        # However, it can be used if specific actions are needed on task selection.
        pass

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
