"""
Task model
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Task:
    """
    Task model
    """

    id: int
    project_id: int
    name: str
    due_date: datetime
    completed: bool = False
