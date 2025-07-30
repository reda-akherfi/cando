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
    type = Column(String(20), default="stopwatch")  # stopwatch, countdown, maduro

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
