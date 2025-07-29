"""
Data initialization service for the Cando application.

This module provides functionality to initialize the database with sample data
for testing and demonstration purposes.
"""

from datetime import datetime, timedelta
from app.services.database import (
    DatabaseService,
    TimerModel,
    TagModel,
    TaskModel,
    ProjectModel,
)


class DataInitializer:
    """
    Service for initializing the database with sample data.

    Creates sample projects, tasks, timers, and tags for demonstration.
    """

    def __init__(self, db_service: DatabaseService):
        """
        Initialize the data initializer.

        Args:
            db_service: Database service for data creation
        """
        self.db_service = db_service

    def initialize_sample_data(self):
        """Initialize the database with sample data."""
        # Create sample projects
        project1 = self.db_service.create_project(
            name="Web Development", description="Building a new website for client"
        )

        project2 = self.db_service.create_project(
            name="Mobile App", description="iOS app development project"
        )

        project3 = self.db_service.create_project(
            name="Research", description="Market research and analysis"
        )

        # Create sample tasks
        task1 = self.db_service.create_task(
            project_id=project1.id,
            name="Design Homepage",
            due_date=datetime.now() + timedelta(days=3),
        )

        task2 = self.db_service.create_task(
            project_id=project1.id,
            name="Implement Backend API",
            due_date=datetime.now() + timedelta(days=7),
        )

        task3 = self.db_service.create_task(
            project_id=project2.id,
            name="UI/UX Design",
            due_date=datetime.now() + timedelta(days=5),
        )

        task4 = self.db_service.create_task(
            project_id=project2.id,
            name="Core Features Development",
            due_date=datetime.now() + timedelta(days=14),
        )

        task5 = self.db_service.create_task(
            project_id=project3.id,
            name="Competitor Analysis",
            due_date=datetime.now() + timedelta(days=2),
        )

        # Create sample tags
        self.db_service.create_tag("Frontend", "task", task1.id)
        self.db_service.create_tag("Backend", "task", task2.id)
        self.db_service.create_tag("Design", "task", task3.id)
        self.db_service.create_tag("Development", "task", task4.id)
        self.db_service.create_tag("Research", "task", task5.id)
        self.db_service.create_tag("High Priority", "project", project1.id)
        self.db_service.create_tag("Medium Priority", "project", project2.id)

        # Create sample timers (completed)
        yesterday = datetime.now() - timedelta(days=1)
        two_days_ago = datetime.now() - timedelta(days=2)

        # Timer for task1 (completed)
        timer1 = self.db_service.create_timer(
            task_id=task1.id,
            start=yesterday.replace(hour=9, minute=0),
            timer_type="stopwatch",
            end=yesterday.replace(hour=12, minute=30),
        )

        # Timer for task2 (completed)
        timer2 = self.db_service.create_timer(
            task_id=task2.id,
            start=yesterday.replace(hour=14, minute=0),
            timer_type="maduro",
            end=yesterday.replace(hour=17, minute=45),
        )

        # Timer for task3 (completed)
        timer3 = self.db_service.create_timer(
            task_id=task3.id,
            start=two_days_ago.replace(hour=10, minute=0),
            timer_type="stopwatch",
            end=two_days_ago.replace(hour=15, minute=30),
        )

        # Timer for task4 (completed)
        timer4 = self.db_service.create_timer(
            task_id=task4.id,
            start=two_days_ago.replace(hour=16, minute=0),
            timer_type="countdown",
            end=two_days_ago.replace(hour=18, minute=0),
        )

        # Timer for task5 (completed)
        timer5 = self.db_service.create_timer(
            task_id=task5.id,
            start=datetime.now().replace(hour=8, minute=0),
            timer_type="stopwatch",
            end=datetime.now().replace(hour=11, minute=15),
        )

        print("Sample data initialized successfully!")
        print(f"Created {3} projects, {5} tasks, {7} tags, and {5} timers")

    def clear_all_data(self):
        """Clear all data from the database."""
        # This is a simple approach - in production you might want more sophisticated cleanup
        with self.db_service.get_session() as session:
            session.query(TimerModel).delete()
            session.query(TagModel).delete()
            session.query(TaskModel).delete()
            session.query(ProjectModel).delete()
            session.commit()

        print("All data cleared from database.")

    def is_database_empty(self) -> bool:
        """
        Check if the database is empty.

        Returns:
            True if database is empty, False otherwise
        """
        projects = self.db_service.get_projects()
        return len(projects) == 0
