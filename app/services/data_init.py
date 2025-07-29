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
        if "Website Redesign" in project.name:
            tasks = [
                ("Design Mockups", "Create wireframes and visual mockups", 8),
                ("Frontend Development", "Implement responsive UI components", 24),
                ("Backend Integration", "Connect frontend with API endpoints", 16),
                ("Testing & QA", "Comprehensive testing and bug fixes", 12),
                ("Deployment", "Deploy to production environment", 4),
            ]
        elif "Mobile App Development" in project.name:
            tasks = [
                ("Project Setup", "Initialize React Native project", 4),
                ("UI Components", "Build reusable UI components", 20),
                ("Navigation", "Implement app navigation", 12),
                ("API Integration", "Connect with backend services", 24),
                ("Testing", "Unit and integration testing", 16),
                ("App Store Prep", "Prepare for app store submission", 8),
            ]
        elif "Database Migration" in project.name:
            tasks = [
                ("Backup Creation", "Create full database backup", 2),
                ("Schema Migration", "Migrate database schema", 16),
                ("Data Migration", "Transfer data to new system", 12),
                ("Testing", "Verify data integrity", 8),
                ("Rollback Plan", "Prepare rollback procedures", 2),
            ]
        elif "API Documentation" in project.name:
            tasks = [
                ("Endpoint Documentation", "Document all API endpoints", 8),
                ("Code Examples", "Create usage examples", 4),
                ("Integration Guide", "Write integration tutorials", 4),
            ]
        elif "Automated Testing Framework" in project.name:
            tasks = [
                ("Framework Setup", "Set up testing infrastructure", 8),
                ("Unit Tests", "Write unit tests for core modules", 20),
                ("Integration Tests", "Create integration test suites", 16),
                ("CI/CD Integration", "Integrate with CI/CD pipeline", 8),
                ("Test Documentation", "Document testing procedures", 8),
            ]
        elif "Security Audit" in project.name:
            tasks = [
                ("Vulnerability Scan", "Run automated security scans", 4),
                ("Code Review", "Manual security code review", 12),
                ("Penetration Testing", "Conduct penetration tests", 6),
                ("Report Generation", "Create security audit report", 2),
            ]
        else:
            # Generic tasks for any project
            tasks = [
                ("Planning", "Project planning and requirements", 4),
                ("Development", "Core development work", 16),
                ("Testing", "Testing and quality assurance", 8),
                ("Deployment", "Deploy to production", 4),
            ]

        for task_name, task_desc, hours in tasks:
            due_date = datetime.now() + timedelta(days=hours // 4)  # Rough estimate
            task = self.db_service.create_task(
                project_id=project.id,
                name=task_name,
                description=task_desc,
                due_date=due_date,
                priority="medium",
            )

            # Note: Task tags are not implemented yet, so we skip adding tags to tasks
            # In the future, we could add: self.db_service.add_task_tag(task.id, "tag_name")

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
