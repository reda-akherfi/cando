"""
Main window view for the Cando application.

This module contains the main window class that manages the application's
primary user interface with tabbed views for different functionality.
"""

from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
)
from app.ui.ui_main import UiMainWindow
from app.ui.chart_widget import (
    TimeByProjectChart,
    DailyProductivityChart,
    TimerTypeChart,
)
from app.services.database import DatabaseService
from app.services.analytics import AnalyticsService
from app.controllers.timer_controller import TimerController


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

        # Create project list
        self.project_list = QListWidget()
        self.project_list.itemClicked.connect(self.on_project_selected)

        # Create task list
        self.task_list = QListWidget()

        # Create buttons
        button_layout = QHBoxLayout()
        add_project_btn = QPushButton("Add Project")
        add_task_btn = QPushButton("Add Task")
        add_project_btn.clicked.connect(self.add_sample_project)
        add_task_btn.clicked.connect(self.add_sample_task)

        button_layout.addWidget(add_project_btn)
        button_layout.addWidget(add_task_btn)

        # Add widgets to layout
        layout.addWidget(QLabel("Projects:"))
        layout.addWidget(self.project_list)
        layout.addWidget(QLabel("Tasks:"))
        layout.addWidget(self.task_list)
        layout.addLayout(button_layout)

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

        # Add settings controls
        clear_data_btn = QPushButton("Clear All Data")
        clear_data_btn.clicked.connect(self.clear_all_data)

        reset_data_btn = QPushButton("Reset to Sample Data")
        reset_data_btn.clicked.connect(self.reset_to_sample_data)

        layout.addWidget(QLabel("Database Settings"))
        layout.addWidget(clear_data_btn)
        layout.addWidget(reset_data_btn)

    def refresh_data(self):
        """Refresh all data displays."""
        self.refresh_project_list()
        self.refresh_charts()

    def refresh_project_list(self):
        """Refresh the project list display."""
        self.project_list.clear()
        projects = self.db_service.get_projects()

        for project in projects:
            item = QListWidgetItem(f"{project.name} - {project.description}")
            item.setData(1, project.id)  # Store project ID
            self.project_list.addItem(item)

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

    def on_project_selected(self, item):
        """Handle project selection."""
        project_id = item.data(1)
        self.refresh_task_list(project_id)

    def refresh_task_list(self, project_id: int):
        """Refresh the task list for a selected project."""
        self.task_list.clear()
        tasks = self.db_service.get_tasks(project_id=project_id)

        for task in tasks:
            status = "✓" if task.completed else "○"
            due_date_str = (
                task.due_date.strftime("%Y-%m-%d") if task.due_date else "No due date"
            )
            item = QListWidgetItem(f"{status} {task.name} (Due: {due_date_str})")
            item.setData(1, task.id)  # Store task ID
            self.task_list.addItem(item)

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

    def add_sample_project(self):
        """Add a sample project for testing."""
        from datetime import datetime

        project = self.db_service.create_project(
            name=f"Sample Project {datetime.now().strftime('%H:%M')}",
            description="Auto-generated sample project",
        )
        self.refresh_project_list()

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
