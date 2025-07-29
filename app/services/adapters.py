"""
Data adapters for the Cando application.

This module provides conversion functions between dataclass models
and SQLAlchemy models for seamless data layer integration.
"""

from typing import List
from app.models.project import Project
from app.models.task import Task
from app.models.tag import Tag
from app.models.timer import Timer
from app.services.database import ProjectModel, TaskModel, TagModel, TimerModel


def project_model_to_dataclass(db_project: ProjectModel) -> Project:
    """Convert SQLAlchemy ProjectModel to dataclass Project."""
    return Project(
        id=db_project.id,
        name=db_project.name,
        description=db_project.description or "",
        tasks=[task.id for task in db_project.tasks],
    )


def project_dataclass_to_model(project: Project) -> ProjectModel:
    """Convert dataclass Project to SQLAlchemy ProjectModel."""
    return ProjectModel(
        id=project.id, name=project.name, description=project.description
    )


def task_model_to_dataclass(db_task: TaskModel) -> Task:
    """Convert SQLAlchemy TaskModel to dataclass Task."""
    return Task(
        id=db_task.id,
        project_id=db_task.project_id,
        name=db_task.name,
        due_date=db_task.due_date,
        completed=db_task.completed,
    )


def task_dataclass_to_model(task: Task) -> TaskModel:
    """Convert dataclass Task to SQLAlchemy TaskModel."""
    return TaskModel(
        id=task.id,
        project_id=task.project_id,
        name=task.name,
        due_date=task.due_date,
        completed=task.completed,
    )


def tag_model_to_dataclass(db_tag: TagModel) -> Tag:
    """Convert SQLAlchemy TagModel to dataclass Tag."""
    return Tag(
        id=db_tag.id,
        name=db_tag.name,
        linked_type=db_tag.linked_type,
        linked_id=db_tag.linked_id,
    )


def tag_dataclass_to_model(tag: Tag) -> TagModel:
    """Convert dataclass Tag to SQLAlchemy TagModel."""
    return TagModel(
        id=tag.id, name=tag.name, linked_type=tag.linked_type, linked_id=tag.linked_id
    )


def timer_model_to_dataclass(db_timer: TimerModel) -> Timer:
    """Convert SQLAlchemy TimerModel to dataclass Timer."""
    return Timer(
        id=db_timer.id,
        task_id=db_timer.task_id,
        start=db_timer.start,
        end=db_timer.end,
        type=db_timer.type,
    )


def timer_dataclass_to_model(timer: Timer) -> TimerModel:
    """Convert dataclass Timer to SQLAlchemy TimerModel."""
    return TimerModel(
        id=timer.id,
        task_id=timer.task_id,
        start=timer.start,
        end=timer.end,
        type=timer.type,
    )


def convert_project_list(db_projects: List[ProjectModel]) -> List[Project]:
    """Convert a list of SQLAlchemy ProjectModels to dataclass Projects."""
    return [project_model_to_dataclass(p) for p in db_projects]


def convert_task_list(db_tasks: List[TaskModel]) -> List[Task]:
    """Convert a list of SQLAlchemy TaskModels to dataclass Tasks."""
    return [task_model_to_dataclass(t) for t in db_tasks]


def convert_tag_list(db_tags: List[TagModel]) -> List[Tag]:
    """Convert a list of SQLAlchemy TagModels to dataclass Tags."""
    return [tag_model_to_dataclass(t) for t in db_tags]


def convert_timer_list(db_timers: List[TimerModel]) -> List[Timer]:
    """Convert a list of SQLAlchemy TimerModels to dataclass Timers."""
    return [timer_model_to_dataclass(t) for t in db_timers]
