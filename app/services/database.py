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
from app.models.habit import Habit, HabitEntry, HabitType, HabitFrequency

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
    color = Column(String(7), nullable=True)  # Hex color code (e.g., #FF5733)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())


class TimerModel(Base):
    """SQLAlchemy model for timers."""

    __tablename__ = "timers"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=True)
    type = Column(String(20), default="stopwatch")  # stopwatch, countdown, pomodoro
    duration = Column(
        Integer, nullable=True
    )  # Duration in seconds for countdown/pomodoro
    pomodoro_session_type = Column(
        String(20), nullable=True
    )  # work, short_break, long_break
    pomodoro_session_number = Column(
        Integer, nullable=True
    )  # Session number in the cycle

    # Relationships
    task = relationship("TaskModel", back_populates="timers")


class ConfigModel(Base):
    """SQLAlchemy model for application configuration."""

    __tablename__ = "config"

    id = Column(Integer, primary_key=True)
    key = Column(String(100), nullable=False, unique=True)
    value = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class HabitModel(Base):
    """SQLAlchemy model for habits."""

    __tablename__ = "habits"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    habit_type = Column(
        String(20), nullable=False
    )  # duration, units, real_number, boolean, rating, count
    frequency = Column(String(20), default="daily")  # daily, weekly, monthly, custom
    custom_interval_days = Column(Integer, nullable=True)
    target_value = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)
    color = Column(String(7), default="#007bff")  # Hex color
    active = Column(Boolean, default=True)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    rating_scale = Column(Integer, default=10)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    entries = relationship(
        "HabitEntryModel", back_populates="habit", cascade="all, delete-orphan"
    )


class HabitEntryModel(Base):
    """SQLAlchemy model for habit entries."""

    __tablename__ = "habit_entries"

    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False)
    date = Column(DateTime, nullable=False)  # Store as date
    value = Column(Float, nullable=False)  # Store all values as float for simplicity
    value_type = Column(String(20), nullable=False)  # float, int, bool, str
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    habit = relationship("HabitModel", back_populates="entries")


class HabitTagModel(Base):
    """SQLAlchemy model for habit tags."""

    __tablename__ = "habit_tags"

    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False)
    tag_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=func.now())


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

    def add_project_tag(
        self, project_id: int, tag_name: str, cascade_to_tasks: bool = True
    ) -> bool:
        """Add a tag to a project and optionally cascade to all its tasks."""
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

            # Check if tag exists elsewhere to get color and description
            existing_tag_info = (
                session.query(TagModel).filter(TagModel.name == tag_name).first()
            )

            # If there's a dummy tag, remove it since we're creating a real one
            if existing_tag_info and existing_tag_info.linked_type == "dummy":
                session.delete(existing_tag_info)
                session.flush()

            # Create new tag for project
            new_tag = TagModel(
                name=tag_name,
                linked_type="project",
                linked_id=project_id,
                color=existing_tag_info.color if existing_tag_info else "#FF5733",
                description=existing_tag_info.description if existing_tag_info else "",
            )
            session.add(new_tag)

            # Cascade to tasks if requested
            if cascade_to_tasks:
                tasks = (
                    session.query(TaskModel)
                    .filter(TaskModel.project_id == project_id)
                    .all()
                )
                for task in tasks:
                    # Check if tag already exists for this task
                    existing_task_tag = (
                        session.query(TagModel)
                        .filter(
                            TagModel.name == tag_name,
                            TagModel.linked_type == "task",
                            TagModel.linked_id == task.id,
                        )
                        .first()
                    )

                    if not existing_task_tag:
                        task_tag = TagModel(
                            name=tag_name,
                            linked_type="task",
                            linked_id=task.id,
                            color=(
                                existing_tag_info.color
                                if existing_tag_info
                                else "#FF5733"
                            ),
                            description=(
                                existing_tag_info.description
                                if existing_tag_info
                                else ""
                            ),
                        )
                        session.add(task_tag)

            session.commit()
            return True

    def add_task_tag(
        self, task_id: int, tag_name: str, cascade_to_project: bool = True
    ) -> bool:
        """Add a tag to a task and optionally cascade to the project if ALL tasks in the project have this tag."""
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

            # Check if tag exists elsewhere to get color and description
            existing_tag_info = (
                session.query(TagModel).filter(TagModel.name == tag_name).first()
            )

            # If there's a dummy tag, remove it since we're creating a real one
            if existing_tag_info and existing_tag_info.linked_type == "dummy":
                session.delete(existing_tag_info)
                session.flush()

            # Create new tag for task
            new_tag = TagModel(
                name=tag_name,
                linked_type="task",
                linked_id=task_id,
                color=existing_tag_info.color if existing_tag_info else "#FF5733",
                description=existing_tag_info.description if existing_tag_info else "",
            )
            session.add(new_tag)

            # Cascade to project if requested
            if cascade_to_project:
                # Get all tasks in the project
                all_tasks_in_project = (
                    session.query(TaskModel)
                    .filter(TaskModel.project_id == task.project_id)
                    .all()
                )

                # Get all tasks in the project that have this tag (including the one we just added)
                # We need to flush the session to make sure our new tag is included in the query
                session.flush()
                tasks_with_tag = (
                    session.query(TagModel)
                    .filter(
                        TagModel.name == tag_name,
                        TagModel.linked_type == "task",
                    )
                    .join(TaskModel, TagModel.linked_id == TaskModel.id)
                    .filter(TaskModel.project_id == task.project_id)
                    .all()
                )

                # If ALL tasks in the project now have this tag, add it to the project
                if len(tasks_with_tag) == len(all_tasks_in_project):
                    # Check if project already has this tag
                    project_tag = (
                        session.query(TagModel)
                        .filter(
                            TagModel.name == tag_name,
                            TagModel.linked_type == "project",
                            TagModel.linked_id == task.project_id,
                        )
                        .first()
                    )

                    if not project_tag:
                        project_tag = TagModel(
                            name=tag_name,
                            linked_type="project",
                            linked_id=task.project_id,
                            color=(
                                existing_tag_info.color
                                if existing_tag_info
                                else "#FF5733"
                            ),
                            description=(
                                existing_tag_info.description
                                if existing_tag_info
                                else ""
                            ),
                        )
                        session.add(project_tag)

            session.commit()
            return True

    def remove_project_tag(
        self, project_id: int, tag_name: str, cascade_to_tasks: bool = True
    ) -> bool:
        """Remove a tag from a project and optionally cascade removal to all its tasks."""
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

                # Cascade removal to tasks if requested
                if cascade_to_tasks:
                    task_tags = (
                        session.query(TagModel)
                        .filter(
                            TagModel.name == tag_name, TagModel.linked_type == "task"
                        )
                        .join(TaskModel, TagModel.linked_id == TaskModel.id)
                        .filter(TaskModel.project_id == project_id)
                        .all()
                    )

                    for task_tag in task_tags:
                        session.delete(task_tag)

                session.commit()
                return True
            return False

    def remove_task_tag(
        self, task_id: int, tag_name: str, cascade_to_project: bool = True
    ) -> bool:
        """Remove a tag from a task and optionally cascade removal to the project if not ALL tasks have this tag."""
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

                # Cascade removal to project if requested
                if cascade_to_project:
                    # Get the task to find its project
                    task = (
                        session.query(TaskModel).filter(TaskModel.id == task_id).first()
                    )
                    if task:
                        # Get all tasks in the project
                        all_tasks_in_project = (
                            session.query(TaskModel)
                            .filter(TaskModel.project_id == task.project_id)
                            .all()
                        )

                        # Flush the session to make sure the deletion is reflected in the query
                        session.flush()

                        # Get all tasks in the project that have this tag
                        tasks_with_tag = (
                            session.query(TagModel)
                            .filter(
                                TagModel.name == tag_name,
                                TagModel.linked_type == "task",
                            )
                            .join(TaskModel, TagModel.linked_id == TaskModel.id)
                            .filter(TaskModel.project_id == task.project_id)
                            .all()
                        )

                        # If not ALL tasks in the project have this tag, remove it from the project
                        # (This implements: "if a project has at least one task without a tag,
                        # the tag should not be considered as applied to the whole project")
                        if len(tasks_with_tag) < len(all_tasks_in_project):
                            project_tag = (
                                session.query(TagModel)
                                .filter(
                                    TagModel.name == tag_name,
                                    TagModel.linked_type == "project",
                                    TagModel.linked_id == task.project_id,
                                )
                                .first()
                            )
                            if project_tag:
                                session.delete(project_tag)

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
            # Get all unique tag names with their colors and descriptions
            tag_info = (
                session.query(TagModel.name, TagModel.color, TagModel.description)
                .distinct()
                .order_by(TagModel.name)
                .all()
            )

            tags = []
            for tag_name, color, description in tag_info:
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
                    color=color or "#FF5733",  # Default color if None
                    description=description or "",
                    usage_count=usage_count,
                    linked_projects=[p[0] for p in linked_projects],
                    linked_tasks=[t[0] for t in linked_tasks],
                )
                tags.append(tag)

            return tags

    def add_tag(
        self, tag_name: str, color: str = "#FF5733", description: str = ""
    ) -> bool:
        """Add a new tag (if it doesn't exist)."""
        with self.get_session() as session:
            # Check if tag already exists (including dummy tags)
            existing_tag = (
                session.query(TagModel).filter(TagModel.name == tag_name).first()
            )

            if existing_tag:
                # If it's a dummy tag, update it with the new color/description
                if existing_tag.linked_type == "dummy":
                    existing_tag.color = color
                    existing_tag.description = description
                    session.commit()
                return True  # Tag already exists

            # Create a dummy tag entry to establish the tag
            # This will be replaced when the tag is actually used
            dummy_tag = TagModel(
                name=tag_name,
                linked_type="dummy",
                linked_id=0,
                color=color,
                description=description,
            )
            session.add(dummy_tag)
            session.commit()
            return True

    def update_tag(
        self, old_name: str, new_name: str, color: str = None, description: str = None
    ) -> bool:
        """Update a tag name, color, and description across all its usages."""
        with self.get_session() as session:
            # Only check for name conflicts if the name is actually being changed
            if old_name != new_name:
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
                if color is not None:
                    tag.color = color
                if description is not None:
                    tag.description = description

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

    def _get_project_tags(self, session, project_id: int) -> List[dict]:
        """Get tags for a project with color and description."""
        tags = (
            session.query(TagModel)
            .filter(TagModel.linked_type == "project", TagModel.linked_id == project_id)
            .all()
        )
        return [
            {
                "name": tag.name,
                "color": tag.color or "#FF5733",
                "description": tag.description or "",
            }
            for tag in tags
        ]

    def _project_model_to_dataclass(
        self, db_project: ProjectModel, tags: List[dict]
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
                self.add_task_tag(db_task.id, tag_name, cascade_to_project=True)

            # Inherit project tags if any
            project_tags = self._get_project_tags(session, db_task.project_id)
            for tag_name in project_tags:
                # Check if tag already exists for this task
                existing_tag = (
                    session.query(TagModel)
                    .filter(
                        TagModel.name == tag_name,
                        TagModel.linked_type == "task",
                        TagModel.linked_id == db_task.id,
                    )
                    .first()
                )
                if not existing_tag:
                    task_tag = TagModel(
                        name=tag_name, linked_type="task", linked_id=db_task.id
                    )
                    session.add(task_tag)

            session.commit()

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
                        self.remove_task_tag(task_id, tag["name"])
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

    def _get_task_tags(self, session, task_id: int) -> List[dict]:
        """Get tags for a task with color and description."""
        tags = (
            session.query(TagModel)
            .filter(TagModel.linked_type == "task", TagModel.linked_id == task_id)
            .all()
        )
        return [
            {
                "name": tag.name,
                "color": tag.color or "#FF5733",
                "description": tag.description or "",
            }
            for tag in tags
        ]

    def _task_model_to_dataclass(self, db_task: TaskModel, tags: List[dict]) -> Task:
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
            duration=db_timer.duration,
            pomodoro_session_type=db_timer.pomodoro_session_type,
            pomodoro_session_number=db_timer.pomodoro_session_number,
        )

    def get_project_tags(self, project_id: int) -> List[dict]:
        """Get all tags for a specific project."""
        with self.get_session() as session:
            tags = (
                session.query(TagModel.name, TagModel.color, TagModel.description)
                .filter(
                    TagModel.linked_type == "project",
                    TagModel.linked_id == project_id,
                )
                .all()
            )
            return [
                {
                    "name": tag[0],
                    "color": tag[1] or "#FF5733",
                    "description": tag[2] or "",
                }
                for tag in tags
            ]

    def get_task_tags(self, task_id: int) -> List[dict]:
        """Get all tags for a specific task."""
        with self.get_session() as session:
            tags = (
                session.query(TagModel.name, TagModel.color, TagModel.description)
                .filter(
                    TagModel.linked_type == "task",
                    TagModel.linked_id == task_id,
                )
                .all()
            )
            return [
                {
                    "name": tag[0],
                    "color": tag[1] or "#FF5733",
                    "description": tag[2] or "",
                }
                for tag in tags
            ]

    def sync_project_tags_to_tasks(self, project_id: int) -> bool:
        """Synchronize project tags to all its tasks (add missing tags to tasks)."""
        with self.get_session() as session:
            # Get project tags
            project_tags = (
                session.query(TagModel.name)
                .filter(
                    TagModel.linked_type == "project",
                    TagModel.linked_id == project_id,
                )
                .all()
            )
            project_tag_names = [tag[0] for tag in project_tags]

            # Get all tasks for this project
            tasks = (
                session.query(TaskModel)
                .filter(TaskModel.project_id == project_id)
                .all()
            )

            for task in tasks:
                # Get current task tags
                task_tags = (
                    session.query(TagModel.name)
                    .filter(
                        TagModel.linked_type == "task",
                        TagModel.linked_id == task.id,
                    )
                    .all()
                )
                task_tag_names = [tag[0] for tag in task_tags]

                # Add missing project tags to task
                for tag_name in project_tag_names:
                    if tag_name not in task_tag_names:
                        task_tag = TagModel(
                            name=tag_name, linked_type="task", linked_id=task.id
                        )
                        session.add(task_tag)

            session.commit()
            return True

    def sync_task_tags_to_project(self, task_id: int) -> bool:
        """Synchronize task tags to project (add task tags to project if not present)."""
        with self.get_session() as session:
            # Get task
            task = session.query(TaskModel).filter(TaskModel.id == task_id).first()
            if not task:
                return False

            # Get task tags
            task_tags = (
                session.query(TagModel.name)
                .filter(
                    TagModel.linked_type == "task",
                    TagModel.linked_id == task_id,
                )
                .all()
            )
            task_tag_names = [tag[0] for tag in task_tags]

            # Get current project tags
            project_tags = (
                session.query(TagModel.name)
                .filter(
                    TagModel.linked_type == "project",
                    TagModel.linked_id == task.project_id,
                )
                .all()
            )
            project_tag_names = [tag[0] for tag in project_tags]

            # Add missing task tags to project
            for tag_name in task_tag_names:
                if tag_name not in project_tag_names:
                    project_tag = TagModel(
                        name=tag_name, linked_type="project", linked_id=task.project_id
                    )
                    session.add(project_tag)

            session.commit()
            return True

    def get_config(self, key: str, default: str = "") -> str:
        """Get a configuration value by key."""
        with self.get_session() as session:
            config = session.query(ConfigModel).filter(ConfigModel.key == key).first()
            return config.value if config else default

    def set_config(self, key: str, value: str) -> bool:
        """Set a configuration value by key."""
        with self.get_session() as session:
            config = session.query(ConfigModel).filter(ConfigModel.key == key).first()
            if config:
                config.value = value
                config.updated_at = func.now()
            else:
                config = ConfigModel(key=key, value=value)
                session.add(config)
            session.commit()
            return True

    def get_all_config(self) -> dict:
        """Get all configuration values as a dictionary."""
        with self.get_session() as session:
            configs = session.query(ConfigModel).all()
            return {config.key: config.value for config in configs}

    def save_timer_settings(self, settings: dict) -> bool:
        """Save timer settings to the database."""
        try:
            # Save countdown settings
            self.set_config(
                "timer_countdown_minutes", str(settings.get("countdown_minutes", 30))
            )
            self.set_config(
                "timer_countdown_seconds", str(settings.get("countdown_seconds", 0))
            )
            self.set_config(
                "timer_countdown_count_down",
                str(settings.get("countdown_count_down", True)),
            )

            # Save pomodoro settings
            self.set_config(
                "timer_work_duration", str(settings.get("work_duration", 25))
            )
            self.set_config(
                "timer_short_break_duration",
                str(settings.get("short_break_duration", 5)),
            )
            self.set_config(
                "timer_long_break_duration",
                str(settings.get("long_break_duration", 15)),
            )
            self.set_config(
                "timer_autostart_breaks", str(settings.get("autostart_breaks", True))
            )
            self.set_config(
                "timer_autostart_work", str(settings.get("autostart_work", True))
            )
            self.set_config(
                "timer_work_count_down", str(settings.get("work_count_down", True))
            )
            self.set_config(
                "timer_short_break_count_down",
                str(settings.get("short_break_count_down", True)),
            )
            self.set_config(
                "timer_long_break_count_down",
                str(settings.get("long_break_count_down", True)),
            )

            return True
        except Exception as e:
            print(f"Error saving timer settings: {e}")
            return False

    def load_timer_settings(self) -> dict:
        """Load timer settings from the database."""
        try:
            return {
                "countdown_minutes": int(
                    self.get_config("timer_countdown_minutes", "30")
                ),
                "countdown_seconds": int(
                    self.get_config("timer_countdown_seconds", "0")
                ),
                "countdown_count_down": self.get_config(
                    "timer_countdown_count_down", "True"
                ).lower()
                == "true",
                "work_duration": int(self.get_config("timer_work_duration", "25")),
                "short_break_duration": int(
                    self.get_config("timer_short_break_duration", "5")
                ),
                "long_break_duration": int(
                    self.get_config("timer_long_break_duration", "15")
                ),
                "autostart_breaks": self.get_config(
                    "timer_autostart_breaks", "True"
                ).lower()
                == "true",
                "autostart_work": self.get_config(
                    "timer_autostart_work", "True"
                ).lower()
                == "true",
                "work_count_down": self.get_config(
                    "timer_work_count_down", "True"
                ).lower()
                == "true",
                "short_break_count_down": self.get_config(
                    "timer_short_break_count_down", "True"
                ).lower()
                == "true",
                "long_break_count_down": self.get_config(
                    "timer_long_break_count_down", "True"
                ).lower()
                == "true",
            }
        except Exception as e:
            print(f"Error loading timer settings: {e}")
            # Return default settings if there's an error
            return {
                "countdown_minutes": 30,
                "countdown_seconds": 0,
                "countdown_count_down": True,
                "work_duration": 25,
                "short_break_duration": 5,
                "long_break_duration": 15,
                "autostart_breaks": True,
                "autostart_work": True,
                "work_count_down": True,
                "short_break_count_down": True,
                "long_break_count_down": True,
            }

    def save_theme_settings(self, theme_config: dict) -> bool:
        """Save theme settings to the database."""
        try:
            import json

            self.set_config("theme_config", json.dumps(theme_config))
            return True
        except Exception as e:
            print(f"Error saving theme settings: {e}")
            return False

    def load_theme_settings(self) -> dict:
        """Load theme settings from the database."""
        try:
            import json

            theme_json = self.get_config("theme_config", None)
            if theme_json:
                return json.loads(theme_json)
        except Exception as e:
            print(f"Error loading theme settings: {e}")
        return None

    def save_general_settings(self, settings: dict) -> bool:
        """Save general settings to the database."""
        try:
            for key, value in settings.items():
                self.set_config(f"general_{key}", str(value))
            return True
        except Exception as e:
            print(f"Error saving general settings: {e}")
            return False

    def load_general_settings(self) -> dict:
        """Load general settings from the database."""
        try:
            return {
                "start_maximized": self.get_config(
                    "general_start_maximized", "False"
                ).lower()
                == "true",
                "auto_save_interval": int(
                    self.get_config("general_auto_save_interval", "5")
                ),
                "language": self.get_config("general_language", "English"),
                "show_tooltips": self.get_config(
                    "general_show_tooltips", "True"
                ).lower()
                == "true",
                "confirm_deletions": self.get_config(
                    "general_confirm_deletions", "True"
                ).lower()
                == "true",
                "show_status_bar": self.get_config(
                    "general_show_status_bar", "True"
                ).lower()
                == "true",
                "chart_update_frequency": int(
                    self.get_config("general_chart_update_frequency", "5")
                ),
                "cache_size": int(self.get_config("general_cache_size", "100")),
            }
        except Exception as e:
            print(f"Error loading general settings: {e}")
            return {
                "start_maximized": False,
                "auto_save_interval": 5,
                "language": "English",
                "show_tooltips": True,
                "confirm_deletions": True,
                "show_status_bar": True,
                "chart_update_frequency": 5,
                "cache_size": 100,
            }

    def save_notification_settings(self, settings: dict) -> bool:
        """Save notification settings to the database."""
        try:
            for key, value in settings.items():
                self.set_config(f"notification_{key}", str(value))
            return True
        except Exception as e:
            print(f"Error saving notification settings: {e}")
            return False

    def load_notification_settings(self) -> dict:
        """Load notification settings from the database."""
        try:
            return {
                "notify_success": self.get_config(
                    "notification_notify_success", "True"
                ).lower()
                == "true",
                "notify_error": self.get_config(
                    "notification_notify_error", "True"
                ).lower()
                == "true",
                "notify_warning": self.get_config(
                    "notification_notify_warning", "True"
                ).lower()
                == "true",
                "notify_info": self.get_config(
                    "notification_notify_info", "True"
                ).lower()
                == "true",
                "duration": int(self.get_config("notification_duration", "5")),
                "position": self.get_config("notification_position", "Top-Right"),
                "sound": self.get_config("notification_sound", "True").lower()
                == "true",
            }
        except Exception as e:
            print(f"Error loading notification settings: {e}")
            return {
                "notify_success": True,
                "notify_error": True,
                "notify_warning": True,
                "notify_info": True,
                "duration": 5,
                "position": "Top-Right",
                "sound": True,
            }

    # Habit CRUD operations
    def create_habit(self, **kwargs) -> Habit:
        """Create a new habit."""
        # Extract tags from kwargs since they're not part of HabitModel
        tags = kwargs.pop("tags", [])

        # Convert enum objects to strings for database storage
        if "habit_type" in kwargs and hasattr(kwargs["habit_type"], "value"):
            kwargs["habit_type"] = kwargs["habit_type"].value
        if "frequency" in kwargs and hasattr(kwargs["frequency"], "value"):
            kwargs["frequency"] = kwargs["frequency"].value

        with self.get_session() as session:
            db_habit = HabitModel(**kwargs)
            session.add(db_habit)
            session.commit()
            session.refresh(db_habit)

            # Add tags
            for tag_name in tags:
                habit_tag = HabitTagModel(habit_id=db_habit.id, tag_name=tag_name)
                session.add(habit_tag)

            session.commit()

            # Get tags for this habit
            habit_tags = self._get_habit_tags(session, db_habit.id)

            return self._habit_model_to_dataclass(db_habit, habit_tags)

    def get_habits(self, active_only: bool = True) -> List[Habit]:
        """Get all habits, optionally filtered by active status."""
        with self.get_session() as session:
            query = session.query(HabitModel)
            if active_only:
                query = query.filter(HabitModel.active == True)

            db_habits = query.all()
            habits = []

            for db_habit in db_habits:
                tags = self._get_habit_tags(session, db_habit.id)
                habits.append(self._habit_model_to_dataclass(db_habit, tags))

            return habits

    def get_habit(self, habit_id: int) -> Optional[Habit]:
        """Get a specific habit by ID."""
        with self.get_session() as session:
            db_habit = (
                session.query(HabitModel).filter(HabitModel.id == habit_id).first()
            )
            if db_habit:
                tags = self._get_habit_tags(session, db_habit.id)
                return self._habit_model_to_dataclass(db_habit, tags)
            return None

    def update_habit(self, habit_id: int, **kwargs) -> Optional[Habit]:
        """Update a habit."""
        # Extract tags from kwargs since they're not part of HabitModel
        tags = kwargs.pop("tags", None)

        # Convert enum objects to strings for database storage
        if "habit_type" in kwargs and hasattr(kwargs["habit_type"], "value"):
            kwargs["habit_type"] = kwargs["habit_type"].value
        if "frequency" in kwargs and hasattr(kwargs["frequency"], "value"):
            kwargs["frequency"] = kwargs["frequency"].value

        with self.get_session() as session:
            db_habit = (
                session.query(HabitModel).filter(HabitModel.id == habit_id).first()
            )
            if db_habit:
                # Update fields
                for key, value in kwargs.items():
                    if hasattr(db_habit, key):
                        setattr(db_habit, key, value)

                db_habit.updated_at = datetime.now()

                # Update tags if provided
                if tags is not None:
                    # Remove existing tags
                    session.query(HabitTagModel).filter(
                        HabitTagModel.habit_id == habit_id
                    ).delete()

                    # Add new tags
                    for tag_name in tags:
                        habit_tag = HabitTagModel(habit_id=habit_id, tag_name=tag_name)
                        session.add(habit_tag)

                session.commit()
                session.refresh(db_habit)

                # Get updated tags
                habit_tags = self._get_habit_tags(session, db_habit.id)
                return self._habit_model_to_dataclass(db_habit, habit_tags)
            return None

    def delete_habit(self, habit_id: int) -> bool:
        """Delete a habit and all its entries."""
        with self.get_session() as session:
            db_habit = (
                session.query(HabitModel).filter(HabitModel.id == habit_id).first()
            )
            if db_habit:
                session.delete(db_habit)
                session.commit()
                return True
            return False

    def add_habit_tag(self, habit_id: int, tag_name: str) -> bool:
        """Add a tag to a habit."""
        with self.get_session() as session:
            # Check if tag already exists
            existing_tag = (
                session.query(HabitTagModel)
                .filter(
                    HabitTagModel.habit_id == habit_id,
                    HabitTagModel.tag_name == tag_name,
                )
                .first()
            )

            if not existing_tag:
                habit_tag = HabitTagModel(habit_id=habit_id, tag_name=tag_name)
                session.add(habit_tag)
                session.commit()
                return True
            return False

    def remove_habit_tag(self, habit_id: int, tag_name: str) -> bool:
        """Remove a tag from a habit."""
        with self.get_session() as session:
            habit_tag = (
                session.query(HabitTagModel)
                .filter(
                    HabitTagModel.habit_id == habit_id,
                    HabitTagModel.tag_name == tag_name,
                )
                .first()
            )

            if habit_tag:
                session.delete(habit_tag)
                session.commit()
                return True
            return False

    def create_habit_entry(self, **kwargs) -> HabitEntry:
        """Create a new habit entry."""
        with self.get_session() as session:
            # Convert value to appropriate type for storage
            value = kwargs.get("value")
            value_type = type(value).__name__

            # Store all values as float for simplicity
            if isinstance(value, bool):
                float_value = 1.0 if value else 0.0
            elif isinstance(value, str):
                float_value = (
                    float(value)
                    if value.replace(".", "").replace("-", "").isdigit()
                    else 0.0
                )
            else:
                float_value = float(value) if value is not None else 0.0

            db_entry = HabitEntryModel(
                habit_id=kwargs["habit_id"],
                date=kwargs["date"],
                value=float_value,
                value_type=value_type,
                notes=kwargs.get("notes"),
            )
            session.add(db_entry)
            session.commit()
            session.refresh(db_entry)

            return self._habit_entry_model_to_dataclass(db_entry)

    def get_habit_entries(self, habit_id: int, days: int = 30) -> List[HabitEntry]:
        """Get habit entries for a specific habit within the last N days."""
        from datetime import timedelta

        with self.get_session() as session:
            start_date = datetime.now() - timedelta(days=days)

            db_entries = (
                session.query(HabitEntryModel)
                .filter(
                    HabitEntryModel.habit_id == habit_id,
                    HabitEntryModel.date >= start_date,
                )
                .order_by(HabitEntryModel.date.desc())
                .all()
            )

            return [self._habit_entry_model_to_dataclass(entry) for entry in db_entries]

    def get_habit_entry(self, entry_id: int) -> Optional[HabitEntry]:
        """Get a specific habit entry by ID."""
        with self.get_session() as session:
            db_entry = (
                session.query(HabitEntryModel)
                .filter(HabitEntryModel.id == entry_id)
                .first()
            )
            if db_entry:
                return self._habit_entry_model_to_dataclass(db_entry)
            return None

    def update_habit_entry(self, entry_id: int, **kwargs) -> Optional[HabitEntry]:
        """Update a habit entry."""
        with self.get_session() as session:
            db_entry = (
                session.query(HabitEntryModel)
                .filter(HabitEntryModel.id == entry_id)
                .first()
            )
            if db_entry:
                # Update fields
                for key, value in kwargs.items():
                    if hasattr(db_entry, key):
                        setattr(db_entry, key, value)

                db_entry.updated_at = datetime.now()
                session.commit()
                session.refresh(db_entry)

                return self._habit_entry_model_to_dataclass(db_entry)
            return None

    def delete_habit_entry(self, entry_id: int) -> bool:
        """Delete a habit entry."""
        with self.get_session() as session:
            db_entry = (
                session.query(HabitEntryModel)
                .filter(HabitEntryModel.id == entry_id)
                .first()
            )
            if db_entry:
                session.delete(db_entry)
                session.commit()
                return True
            return False

    def _get_habit_tags(self, session, habit_id: int) -> List[str]:
        """Get tags for a habit."""
        db_tags = (
            session.query(HabitTagModel)
            .filter(HabitTagModel.habit_id == habit_id)
            .all()
        )
        return [tag.tag_name for tag in db_tags]

    def _habit_model_to_dataclass(self, db_habit: HabitModel, tags: List[str]) -> Habit:
        """Convert HabitModel to Habit dataclass."""
        # Get recent entries for this habit
        recent_entries = self.get_habit_entries(db_habit.id, days=30)

        return Habit(
            id=db_habit.id,
            name=db_habit.name,
            description=db_habit.description,
            habit_type=HabitType(db_habit.habit_type),
            frequency=HabitFrequency(db_habit.frequency),
            custom_interval_days=db_habit.custom_interval_days,
            target_value=db_habit.target_value,
            unit=db_habit.unit,
            color=db_habit.color,
            active=db_habit.active,
            min_value=db_habit.min_value,
            max_value=db_habit.max_value,
            rating_scale=db_habit.rating_scale,
            created_at=db_habit.created_at,
            updated_at=db_habit.updated_at,
            tags=tags,
            recent_entries=recent_entries,
        )

    def _habit_entry_model_to_dataclass(self, db_entry: HabitEntryModel) -> HabitEntry:
        """Convert HabitEntryModel to HabitEntry dataclass."""
        # Convert stored float value back to original type
        value = db_entry.value
        if db_entry.value_type == "bool":
            value = bool(db_entry.value)
        elif db_entry.value_type == "int":
            value = int(db_entry.value)
        elif db_entry.value_type == "str":
            value = str(db_entry.value)

        return HabitEntry(
            id=db_entry.id,
            habit_id=db_entry.habit_id,
            date=db_entry.date.date(),  # Convert datetime to date
            value=value,
            notes=db_entry.notes,
            created_at=db_entry.created_at,
            updated_at=db_entry.updated_at,
        )
