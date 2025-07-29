"""
Data initialization service for the Cando application.

This module provides functionality to initialize the database with sample data
and manage database state.
"""

from datetime import datetime, timedelta
from typing import List
from app.services.database import DatabaseService


class DataInitializer:
    """Service for initializing and managing database data."""

    def __init__(self, db_service: DatabaseService):
        """Initialize the data initializer."""
        self.db_service = db_service

    def initialize_sample_data(self):
        """Initialize the database with sample data."""
        # Create sample projects
        projects = self.create_sample_projects()

        # Create sample tasks for each project
        for project in projects:
            self.create_sample_tasks(project)

        # Create sample timers
        self.create_sample_timers()

    def create_sample_projects(self) -> List:
        """Create sample projects with enhanced data."""
        projects = []

        # Project 1: Web Development
        web_project = self.db_service.create_project(
            name="Website Redesign",
            description="Complete redesign of company website with modern UI/UX and improved performance",
            due_date=datetime.now() + timedelta(days=30),
            estimated_hours=80.0,
            priority="high",
            status="active",
        )
        self.db_service.add_project_tag(web_project.id, "web")
        self.db_service.add_project_tag(web_project.id, "design")
        self.db_service.add_project_tag(web_project.id, "frontend")
        projects.append(web_project)

        # Project 2: Mobile App
        mobile_project = self.db_service.create_project(
            name="Mobile App Development",
            description="Cross-platform mobile application for iOS and Android using React Native",
            due_date=datetime.now() + timedelta(days=60),
            estimated_hours=120.0,
            priority="urgent",
            status="active",
        )
        self.db_service.add_project_tag(mobile_project.id, "mobile")
        self.db_service.add_project_tag(mobile_project.id, "react-native")
        self.db_service.add_project_tag(mobile_project.id, "cross-platform")
        projects.append(mobile_project)

        # Project 3: Database Migration
        db_project = self.db_service.create_project(
            name="Database Migration",
            description="Migrate legacy database to new cloud-based solution with improved performance",
            due_date=datetime.now() + timedelta(days=15),
            estimated_hours=40.0,
            priority="high",
            status="paused",
        )
        self.db_service.add_project_tag(db_project.id, "database")
        self.db_service.add_project_tag(db_project.id, "migration")
        self.db_service.add_project_tag(db_project.id, "cloud")
        projects.append(db_project)

        # Project 4: Documentation
        doc_project = self.db_service.create_project(
            name="API Documentation",
            description="Create comprehensive API documentation with examples and integration guides",
            due_date=datetime.now() + timedelta(days=7),
            estimated_hours=16.0,
            priority="medium",
            status="active",
        )
        self.db_service.add_project_tag(doc_project.id, "documentation")
        self.db_service.add_project_tag(doc_project.id, "api")
        projects.append(doc_project)

        # Project 5: Testing Framework
        test_project = self.db_service.create_project(
            name="Automated Testing Framework",
            description="Implement comprehensive automated testing suite for all applications",
            due_date=datetime.now() + timedelta(days=45),
            estimated_hours=60.0,
            priority="medium",
            status="active",
        )
        self.db_service.add_project_tag(test_project.id, "testing")
        self.db_service.add_project_tag(test_project.id, "automation")
        self.db_service.add_project_tag(test_project.id, "qa")
        projects.append(test_project)

        # Project 6: Completed Project
        completed_project = self.db_service.create_project(
            name="Security Audit",
            description="Comprehensive security audit of all systems and applications",
            due_date=datetime.now() - timedelta(days=5),
            estimated_hours=24.0,
            priority="high",
            status="completed",
            completed_at=datetime.now() - timedelta(days=2),
        )
        self.db_service.add_project_tag(completed_project.id, "security")
        self.db_service.add_project_tag(completed_project.id, "audit")
        projects.append(completed_project)

        return projects

    def create_sample_tasks(self, project):
        """Create sample tasks for a project."""
        # Define tasks based on project name
        if "Website" in project.name:
            tasks = [
                (
                    "Design Homepage",
                    "Create wireframes and mockups for the homepage",
                    8,
                ),
                ("Implement Navigation", "Build responsive navigation menu", 4),
                (
                    "Add Contact Form",
                    "Create and style contact form with validation",
                    6,
                ),
                ("Optimize Performance", "Optimize images and implement caching", 5),
            ]
        elif "Mobile App" in project.name:
            tasks = [
                ("Setup Development Environment", "Install SDK and configure tools", 3),
                ("Design UI Components", "Create reusable UI components", 10),
                ("Implement Authentication", "Add user login and registration", 8),
                ("Add Push Notifications", "Configure push notification system", 6),
            ]
        elif "Database" in project.name:
            tasks = [
                ("Design Schema", "Create database schema and relationships", 6),
                (
                    "Implement CRUD Operations",
                    "Build create, read, update, delete functions",
                    8,
                ),
                (
                    "Add Data Validation",
                    "Implement input validation and constraints",
                    4,
                ),
                ("Create Backup System", "Setup automated backup procedures", 3),
            ]
        elif "API" in project.name:
            tasks = [
                ("Define Endpoints", "Design REST API endpoints", 5),
                ("Implement Authentication", "Add JWT token authentication", 7),
                ("Add Rate Limiting", "Implement API rate limiting", 4),
                ("Write Documentation", "Create comprehensive API documentation", 6),
            ]
        elif "Marketing" in project.name:
            tasks = [
                (
                    "Research Competitors",
                    "Analyze competitor strategies and positioning",
                    4,
                ),
                ("Create Content Calendar", "Plan content strategy and schedule", 3),
                (
                    "Design Campaign Materials",
                    "Create graphics and copy for campaigns",
                    8,
                ),
                ("Setup Analytics", "Configure tracking and reporting tools", 5),
            ]
        else:  # Default tasks for other projects
            tasks = [
                ("Project Planning", "Define scope, timeline, and deliverables", 4),
                ("Requirements Gathering", "Collect and document requirements", 6),
                ("Implementation", "Build the core functionality", 12),
                ("Testing", "Test and validate the implementation", 5),
                ("Deployment", "Deploy to production environment", 3),
            ]

        for task_name, task_desc, hours in tasks:
            due_date = datetime.now() + timedelta(days=hours // 4)  # Rough estimate
            task = self.db_service.create_task(
                project_id=project.id,
                name=task_name,
                description=task_desc,
                due_date=due_date,
                priority="medium",
                estimated_hours=hours,
            )

            # Add tags to tasks based on project type
            if "Website" in project.name:
                self.db_service.add_task_tag(task.id, "frontend")
                self.db_service.add_task_tag(task.id, "web")
            elif "Mobile App" in project.name:
                self.db_service.add_task_tag(task.id, "mobile")
                self.db_service.add_task_tag(task.id, "app")
            elif "Database" in project.name:
                self.db_service.add_task_tag(task.id, "backend")
                self.db_service.add_task_tag(task.id, "database")
            elif "API" in project.name:
                self.db_service.add_task_tag(task.id, "backend")
                self.db_service.add_task_tag(task.id, "api")
            elif "Marketing" in project.name:
                self.db_service.add_task_tag(task.id, "marketing")
                self.db_service.add_task_tag(task.id, "content")
            else:
                self.db_service.add_task_tag(task.id, "general")
                self.db_service.add_task_tag(task.id, "planning")

    def create_sample_timers(self):
        """Create sample timer data."""
        tasks = self.db_service.get_tasks()
        if not tasks:
            return

        # Create some sample timers for the first few tasks
        for i, task in enumerate(tasks[:5]):
            # Create a timer that was started and completed
            start_time = datetime.now() - timedelta(hours=2 + i)
            end_time = start_time + timedelta(hours=1 + (i * 0.5))

            timer = self.db_service.create_timer(
                task_id=task.id, start=start_time, end=end_time, type="stopwatch"
            )

    def is_database_empty(self) -> bool:
        """Check if the database is empty."""
        with self.db_service.get_session() as session:
            from app.services.database import ProjectModel

            count = session.query(ProjectModel).count()
            return count == 0

    def clear_all_data(self):
        """Clear all data from the database."""
        with self.db_service.get_session() as session:
            from app.services.database import (
                TimerModel,
                TagModel,
                TaskModel,
                ProjectModel,
            )

            session.query(TimerModel).delete()
            session.query(TagModel).delete()
            session.query(TaskModel).delete()
            session.query(ProjectModel).delete()
            session.commit()
