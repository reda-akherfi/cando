"""
Database service for the Cando application.

This module provides SQLAlchemy ORM models and database operations
for the productivity application.
"""

from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Float,
    Text,
    ForeignKey,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from app.models.project import Project
from app.models.task import Task
from app.models.tag import Tag
from app.models.timer import Timer

Base = declarative_base()


class ProjectModel(Base):
    """SQLAlchemy model for projects."""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    estimated_hours = Column(Float, nullable=True)
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    status = Column(
        String(20), default="active"
    )  # active, completed, paused, cancelled
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    tasks = relationship(
        "TaskModel", back_populates="project", cascade="all, delete-orphan"
    )


class TaskModel(Base):
    """SQLAlchemy model for tasks."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)
    due_date = Column(DateTime, nullable=True)
    estimated_hours = Column(Float, nullable=True)
    priority = Column(String(20), default="medium")
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
    type = Column(String(20), default="stopwatch")  # stopwatch, countdown, maduro
    created_at = Column(DateTime, default=func.now())

    # Relationships
    task = relationship("TaskModel", back_populates="timers")


class DatabaseService:
    """Service class for database operations."""

    def __init__(self, db_url: str = "sqlite:///cando.db"):
        """Initialize database service."""
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def get_session(self):
        """Get database session."""
        return self.SessionLocal()

    # Project CRUD operations
    def create_project(self, **kwargs) -> Project:
        """Create a new project."""
        # Extract tags from kwargs since they're not part of ProjectModel
        tags = kwargs.pop("tags", [])

        with self.get_session() as session:
            db_project = ProjectModel(**kwargs)
            session.add(db_project)
            session.commit()
            session.refresh(db_project)

            # Get tags for this project
            project_tags = self._get_project_tags(session, db_project.id)

            return self._project_model_to_dataclass(db_project, project_tags)

    def get_projects(self, status: Optional[str] = None) -> List[Project]:
        """Get all projects, optionally filtered by status."""
        with self.get_session() as session:
            query = session.query(ProjectModel)
            if status:
                query = query.filter(ProjectModel.status == status)

            db_projects = query.all()
            projects = []

            for db_project in db_projects:
                tags = self._get_project_tags(session, db_project.id)
                projects.append(self._project_model_to_dataclass(db_project, tags))

            return projects

    def get_project(self, project_id: int) -> Optional[Project]:
        """Get a specific project by ID."""
        with self.get_session() as session:
            db_project = (
                session.query(ProjectModel)
                .filter(ProjectModel.id == project_id)
                .first()
            )
            if db_project:
                tags = self._get_project_tags(session, db_project.id)
                return self._project_model_to_dataclass(db_project, tags)
            return None

    def update_project(self, project_id: int, **kwargs) -> Optional[Project]:
        """Update a project."""
        # Extract tags from kwargs since they're not part of ProjectModel
        tags = kwargs.pop("tags", None)

        with self.get_session() as session:
            db_project = (
                session.query(ProjectModel)
                .filter(ProjectModel.id == project_id)
                .first()
            )
            if db_project:
                # Update fields
                for key, value in kwargs.items():
                    if hasattr(db_project, key):
                        setattr(db_project, key, value)

                db_project.updated_at = datetime.now()
                session.commit()
                session.refresh(db_project)

                # Get updated tags
                project_tags = self._get_project_tags(session, db_project.id)
                return self._project_model_to_dataclass(db_project, project_tags)
            return None

    def delete_project(self, project_id: int) -> bool:
        """Delete a project."""
        with self.get_session() as session:
            db_project = (
                session.query(ProjectModel)
                .filter(ProjectModel.id == project_id)
                .first()
            )
            if db_project:
                session.delete(db_project)
                session.commit()
                return True
            return False

    def add_project_tag(self, project_id: int, tag_name: str) -> bool:
        """Add a tag to a project."""
        with self.get_session() as session:
            # Check if project exists
            project = (
                session.query(ProjectModel)
                .filter(ProjectModel.id == project_id)
                .first()
            )
            if not project:
                return False

            # Check if tag already exists for this project
            existing_tag = (
                session.query(TagModel)
                .filter(
                    TagModel.name == tag_name,
                    TagModel.linked_type == "project",
                    TagModel.linked_id == project_id,
                )
                .first()
            )

            if existing_tag:
                return False  # Tag already exists for this project

            # Create new tag
            new_tag = TagModel(
                name=tag_name, linked_type="project", linked_id=project_id
            )
            session.add(new_tag)
            session.commit()
            return True

    def add_task_tag(self, task_id: int, tag_name: str) -> bool:
        """Add a tag to a task."""
        with self.get_session() as session:
            # Check if task exists
            task = session.query(TaskModel).filter(TaskModel.id == task_id).first()
            if not task:
                return False

            # Check if tag already exists for this task
            existing_tag = (
                session.query(TagModel)
                .filter(
                    TagModel.name == tag_name,
                    TagModel.linked_type == "task",
                    TagModel.linked_id == task_id,
                )
                .first()
            )

            if existing_tag:
                return False  # Tag already exists for this task

            # Create new tag
            new_tag = TagModel(name=tag_name, linked_type="task", linked_id=task_id)
            session.add(new_tag)
            session.commit()
            return True

    def remove_project_tag(self, project_id: int, tag_name: str) -> bool:
        """Remove a tag from a project."""
        with self.get_session() as session:
            tag = (
                session.query(TagModel)
                .filter(
                    TagModel.name == tag_name,
                    TagModel.linked_type == "project",
                    TagModel.linked_id == project_id,
                )
                .first()
            )

            if tag:
                session.delete(tag)
                session.commit()
                return True
            return False

    def remove_task_tag(self, task_id: int, tag_name: str) -> bool:
        """Remove a tag from a task."""
        with self.get_session() as session:
            tag = (
                session.query(TagModel)
                .filter(
                    TagModel.name == tag_name,
                    TagModel.linked_type == "task",
                    TagModel.linked_id == task_id,
                )
                .first()
            )

            if tag:
                session.delete(tag)
                session.commit()
                return True
            return False

    def get_all_tags(self) -> List[str]:
        """Get all unique tags used across projects and tasks."""
        with self.get_session() as session:
            tags = session.query(TagModel.name).distinct().all()
            return [tag[0] for tag in tags]

    def get_tags_by_type(self, linked_type: str) -> List[str]:
        """Get all unique tags for a specific type (project or task)."""
        with self.get_session() as session:
            tags = (
                session.query(TagModel.name)
                .filter(TagModel.linked_type == linked_type)
                .distinct()
                .all()
            )
            return [tag[0] for tag in tags]

    def get_tags(self) -> List[Tag]:
        """Get all tags with usage statistics."""
        with self.get_session() as session:
            # Get all unique tag names
            tag_names = (
                session.query(TagModel.name).distinct().order_by(TagModel.name).all()
            )

            tags = []
            for (tag_name,) in tag_names:
                # Count usage for this tag
                usage_count = (
                    session.query(TagModel).filter(TagModel.name == tag_name).count()
                )

                # Get linked items (projects and tasks)
                linked_projects = (
                    session.query(TagModel.linked_id)
                    .filter(
                        TagModel.name == tag_name, TagModel.linked_type == "project"
                    )
                    .all()
                )

                linked_tasks = (
                    session.query(TagModel.linked_id)
                    .filter(TagModel.name == tag_name, TagModel.linked_type == "task")
                    .all()
                )

                tag = Tag(
                    id=len(tags) + 1,  # Simple ID for display
                    name=tag_name,
                    usage_count=usage_count,
                    linked_projects=[p[0] for p in linked_projects],
                    linked_tasks=[t[0] for t in linked_tasks],
                )
                tags.append(tag)

            return tags

    def add_tag(self, tag_name: str) -> bool:
        """Add a new tag (if it doesn't exist)."""
        with self.get_session() as session:
            # Check if tag already exists
            existing_tag = (
                session.query(TagModel).filter(TagModel.name == tag_name).first()
            )

            if existing_tag:
                return False  # Tag already exists

            # Create a dummy tag entry to establish the tag
            # This will be replaced when the tag is actually used
            dummy_tag = TagModel(name=tag_name, linked_type="dummy", linked_id=0)
            session.add(dummy_tag)
            session.commit()
            return True

    def update_tag(self, old_name: str, new_name: str) -> bool:
        """Update a tag name across all its usages."""
        with self.get_session() as session:
            # Check if new name already exists
            existing_tag = (
                session.query(TagModel).filter(TagModel.name == new_name).first()
            )

            if existing_tag:
                return False  # New name already exists

            # Update all instances of the old tag name
            tags_to_update = (
                session.query(TagModel).filter(TagModel.name == old_name).all()
            )

            for tag in tags_to_update:
                tag.name = new_name

            session.commit()
            return True

    def delete_tag(self, tag_name: str) -> bool:
        """Delete a tag and all its usages."""
        with self.get_session() as session:
            tags_to_delete = (
                session.query(TagModel).filter(TagModel.name == tag_name).all()
            )

            if not tags_to_delete:
                return False

            for tag in tags_to_delete:
                session.delete(tag)

            session.commit()
            return True

    def get_tag_usage_stats(self) -> List[Tuple[str, int]]:
        """Get tag usage statistics sorted by popularity."""
        with self.get_session() as session:
            # Get tag usage counts
            tag_counts = (
                session.query(TagModel.name, func.count(TagModel.id))
                .group_by(TagModel.name)
                .order_by(func.count(TagModel.id).desc())
                .all()
            )

            return [(name, count) for name, count in tag_counts]

    def _get_project_tags(self, session, project_id: int) -> List[str]:
        """Get tags for a project."""
        tags = (
            session.query(TagModel)
            .filter(TagModel.linked_type == "project", TagModel.linked_id == project_id)
            .all()
        )
        return [tag.name for tag in tags]

    def _project_model_to_dataclass(
        self, db_project: ProjectModel, tags: List[str]
    ) -> Project:
        """Convert ProjectModel to Project dataclass."""
        return Project(
            id=db_project.id,
            name=db_project.name,
            description=db_project.description or "",
            due_date=db_project.due_date,
            estimated_hours=db_project.estimated_hours,
            priority=db_project.priority,
            status=db_project.status,
            tags=tags,
            created_at=db_project.created_at,
            updated_at=db_project.updated_at,
            completed_at=db_project.completed_at,
        )

    # Task CRUD operations
    def create_task(self, **kwargs) -> Task:
        """Create a new task."""
        # Extract tags from kwargs since they're not part of TaskModel
        tags = kwargs.pop("tags", [])

        with self.get_session() as session:
            db_task = TaskModel(**kwargs)
            session.add(db_task)
            session.commit()
            session.refresh(db_task)

            # Add tags separately
            for tag_name in tags:
                self.add_task_tag(db_task.id, tag_name)

            # Get tags for this task
            task_tags = self._get_task_tags(session, db_task.id)

            return self._task_model_to_dataclass(db_task, task_tags)

    def get_tasks(self, project_id: Optional[int] = None) -> List[Task]:
        """Get all tasks, optionally filtered by project."""
        with self.get_session() as session:
            query = session.query(TaskModel)
            if project_id:
                query = query.filter(TaskModel.project_id == project_id)

            db_tasks = query.all()
            tasks = []

            for db_task in db_tasks:
                task_tags = self._get_task_tags(session, db_task.id)
                task = self._task_model_to_dataclass(db_task, task_tags)
                tasks.append(task)

            return tasks

    def get_task(self, task_id: int) -> Optional[Task]:
        """Get a specific task by ID."""
        with self.get_session() as session:
            db_task = session.query(TaskModel).filter(TaskModel.id == task_id).first()
            if db_task:
                task_tags = self._get_task_tags(session, db_task.id)
                return self._task_model_to_dataclass(db_task, task_tags)
            return None

    def update_task(self, task_id: int, **kwargs) -> Optional[Task]:
        """Update a task."""
        # Extract tags from kwargs since they're not part of TaskModel
        tags = kwargs.pop("tags", None)

        with self.get_session() as session:
            db_task = session.query(TaskModel).filter(TaskModel.id == task_id).first()
            if db_task:
                # Update fields
                for key, value in kwargs.items():
                    if hasattr(db_task, key):
                        setattr(db_task, key, value)

                db_task.updated_at = datetime.now()
                session.commit()
                session.refresh(db_task)

                # Update tags if provided
                if tags is not None:
                    # Remove old tags
                    current_tags = self._get_task_tags(session, task_id)
                    for tag in current_tags:
                        self.remove_task_tag(task_id, tag)
                    # Add new tags
                    for tag in tags:
                        self.add_task_tag(task_id, tag)

                # Get updated tags
                task_tags = self._get_task_tags(session, db_task.id)
                return self._task_model_to_dataclass(db_task, task_tags)
            return None

    def delete_task(self, task_id: int) -> bool:
        """Delete a task."""
        with self.get_session() as session:
            db_task = session.query(TaskModel).filter(TaskModel.id == task_id).first()
            if db_task:
                session.delete(db_task)
                session.commit()
                return True
            return False

    def _get_task_tags(self, session, task_id: int) -> List[str]:
        """Get tags for a task."""
        tags = (
            session.query(TagModel)
            .filter(TagModel.linked_type == "task", TagModel.linked_id == task_id)
            .all()
        )
        return [tag.name for tag in tags]

    def _task_model_to_dataclass(self, db_task: TaskModel, tags: List[str]) -> Task:
        """Convert TaskModel to Task dataclass."""
        return Task(
            id=db_task.id,
            project_id=db_task.project_id,
            name=db_task.name,
            description=db_task.description or "",
            completed=db_task.completed,
            due_date=db_task.due_date,
            estimated_hours=db_task.estimated_hours,
            priority=db_task.priority,
            tags=tags,
            created_at=db_task.created_at,
            updated_at=db_task.updated_at,
        )

    # Timer CRUD operations
    def create_timer(self, **kwargs) -> Timer:
        """Create a new timer."""
        with self.get_session() as session:
            db_timer = TimerModel(**kwargs)
            session.add(db_timer)
            session.commit()
            session.refresh(db_timer)
            return self._timer_model_to_dataclass(db_timer)

    def get_timers(self, task_id: Optional[int] = None) -> List[Timer]:
        """Get all timers, optionally filtered by task."""
        with self.get_session() as session:
            query = session.query(TimerModel)
            if task_id:
                query = query.filter(TimerModel.task_id == task_id)

            db_timers = query.all()
            return [self._timer_model_to_dataclass(timer) for timer in db_timers]

    def update_timer(self, timer_id: int, **kwargs) -> Optional[Timer]:
        """Update a timer."""
        with self.get_session() as session:
            db_timer = (
                session.query(TimerModel).filter(TimerModel.id == timer_id).first()
            )
            if db_timer:
                for key, value in kwargs.items():
                    if hasattr(db_timer, key):
                        setattr(db_timer, key, value)
                session.commit()
                session.refresh(db_timer)
                return self._timer_model_to_dataclass(db_timer)
            return None

    def _timer_model_to_dataclass(self, db_timer: TimerModel) -> Timer:
        """Convert TimerModel to Timer dataclass."""
        return Timer(
            id=db_timer.id,
            task_id=db_timer.task_id,
            start=db_timer.start,
            end=db_timer.end,
            type=db_timer.type,
        )
