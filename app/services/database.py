"""
Database service for the Cando application.

This module provides SQLAlchemy-based data persistence using SQLite.
It includes database models, session management, and CRUD operations.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.sql import func

Base = declarative_base()


class ProjectModel(Base):
    """SQLAlchemy model for projects."""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    tasks = relationship(
        "TaskModel", back_populates="project", cascade="all, delete-orphan"
    )


class TaskModel(Base):
    """SQLAlchemy model for tasks."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    due_date = Column(DateTime, nullable=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("ProjectModel", back_populates="tasks")
    timers = relationship(
        "TimerModel", back_populates="task", cascade="all, delete-orphan"
    )


class TagModel(Base):
    """SQLAlchemy model for tags."""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    linked_type = Column(String(20), nullable=False)  # 'project' or 'task'
    linked_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())


class TimerModel(Base):
    """SQLAlchemy model for timers."""

    __tablename__ = "timers"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=True)
    type = Column(String(50), nullable=False)  # 'maduro', 'countdown', 'stopwatch'
    created_at = Column(DateTime, default=func.now())

    # Relationships
    task = relationship("TaskModel", back_populates="timers")


class DatabaseService:
    """
    Service for managing database operations.

    Provides CRUD operations for all entities and database session management.
    """

    def __init__(self, db_url: str = "sqlite:///cando.db"):
        """
        Initialize the database service.

        Args:
            db_url: SQLAlchemy database URL
        """
        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # Create tables
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    # Project CRUD operations
    def create_project(self, name: str, description: str = "") -> ProjectModel:
        """Create a new project."""
        with self.get_session() as session:
            project = ProjectModel(name=name, description=description)
            session.add(project)
            session.commit()
            session.refresh(project)
            return project

    def get_projects(self) -> List[ProjectModel]:
        """Get all projects."""
        with self.get_session() as session:
            return session.query(ProjectModel).all()

    def get_project(self, project_id: int) -> Optional[ProjectModel]:
        """Get a project by ID."""
        with self.get_session() as session:
            return (
                session.query(ProjectModel)
                .filter(ProjectModel.id == project_id)
                .first()
            )

    def update_project(
        self, project_id: int, name: str = None, description: str = None
    ) -> Optional[ProjectModel]:
        """Update a project."""
        with self.get_session() as session:
            project = (
                session.query(ProjectModel)
                .filter(ProjectModel.id == project_id)
                .first()
            )
            if project:
                if name is not None:
                    project.name = name
                if description is not None:
                    project.description = description
                session.commit()
                session.refresh(project)
            return project

    def delete_project(self, project_id: int) -> bool:
        """Delete a project."""
        with self.get_session() as session:
            project = (
                session.query(ProjectModel)
                .filter(ProjectModel.id == project_id)
                .first()
            )
            if project:
                session.delete(project)
                session.commit()
                return True
            return False

    # Task CRUD operations
    def create_task(
        self, project_id: int, name: str, due_date: datetime = None
    ) -> TaskModel:
        """Create a new task."""
        with self.get_session() as session:
            task = TaskModel(project_id=project_id, name=name, due_date=due_date)
            session.add(task)
            session.commit()
            session.refresh(task)
            return task

    def get_tasks(self, project_id: int = None) -> List[TaskModel]:
        """Get all tasks, optionally filtered by project."""
        with self.get_session() as session:
            query = session.query(TaskModel)
            if project_id:
                query = query.filter(TaskModel.project_id == project_id)
            return query.all()

    def get_task(self, task_id: int) -> Optional[TaskModel]:
        """Get a task by ID."""
        with self.get_session() as session:
            return session.query(TaskModel).filter(TaskModel.id == task_id).first()

    def update_task(
        self,
        task_id: int,
        name: str = None,
        due_date: datetime = None,
        completed: bool = None,
    ) -> Optional[TaskModel]:
        """Update a task."""
        with self.get_session() as session:
            task = session.query(TaskModel).filter(TaskModel.id == task_id).first()
            if task:
                if name is not None:
                    task.name = name
                if due_date is not None:
                    task.due_date = due_date
                if completed is not None:
                    task.completed = completed
                session.commit()
                session.refresh(task)
            return task

    def delete_task(self, task_id: int) -> bool:
        """Delete a task."""
        with self.get_session() as session:
            task = session.query(TaskModel).filter(TaskModel.id == task_id).first()
            if task:
                session.delete(task)
                session.commit()
                return True
            return False

    # Timer CRUD operations
    def create_timer(
        self, task_id: int, start: datetime, timer_type: str, end: datetime = None
    ) -> TimerModel:
        """Create a new timer."""
        with self.get_session() as session:
            timer = TimerModel(task_id=task_id, start=start, end=end, type=timer_type)
            session.add(timer)
            session.commit()
            session.refresh(timer)
            return timer

    def get_timers(self, task_id: int = None) -> List[TimerModel]:
        """Get all timers, optionally filtered by task."""
        with self.get_session() as session:
            query = session.query(TimerModel)
            if task_id:
                query = query.filter(TimerModel.task_id == task_id)
            return query.all()

    def update_timer(self, timer_id: int, end: datetime = None) -> Optional[TimerModel]:
        """Update a timer (typically to set end time)."""
        with self.get_session() as session:
            timer = session.query(TimerModel).filter(TimerModel.id == timer_id).first()
            if timer and end is not None:
                timer.end = end
                session.commit()
                session.refresh(timer)
            return timer

    # Tag CRUD operations
    def create_tag(self, name: str, linked_type: str, linked_id: int) -> TagModel:
        """Create a new tag."""
        with self.get_session() as session:
            tag = TagModel(name=name, linked_type=linked_type, linked_id=linked_id)
            session.add(tag)
            session.commit()
            session.refresh(tag)
            return tag

    def get_tags(
        self, linked_type: str = None, linked_id: int = None
    ) -> List[TagModel]:
        """Get all tags, optionally filtered by linked entity."""
        with self.get_session() as session:
            query = session.query(TagModel)
            if linked_type:
                query = query.filter(TagModel.linked_type == linked_type)
            if linked_id:
                query = query.filter(TagModel.linked_id == linked_id)
            return query.all()

    def delete_tag(self, tag_id: int) -> bool:
        """Delete a tag."""
        with self.get_session() as session:
            tag = session.query(TagModel).filter(TagModel.id == tag_id).first()
            if tag:
                session.delete(tag)
                session.commit()
                return True
            return False
