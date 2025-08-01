"""
Data initialization service for the Cando application.

This module provides functionality to initialize the database with default configuration
and manage database state.
"""

from app.services.database import DatabaseService


class DataInitializer:
    """Service for initializing and managing database data."""

    def __init__(self, db_service: DatabaseService):
        """Initialize the data initializer."""
        self.db_service = db_service

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
                ConfigModel,
            )

            session.query(TimerModel).delete()
            session.query(TagModel).delete()
            session.query(TaskModel).delete()
            session.query(ProjectModel).delete()
            session.query(ConfigModel).delete()
            session.commit()

    def initialize_default_config(self):
        """Initialize default configuration settings."""
        # Set default settings
        self.db_service.set_config("always_maximized", "true")
        self.db_service.set_config("theme", "dark")
