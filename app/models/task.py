"""
Task model for the Cando application.

This module defines the Task dataclass that represents a task
in the productivity application.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Task:
    """
    Task entity representing a work task.

    A task is a specific piece of work that belongs to a project
    and can be tracked with timers.
    """

    id: Optional[int] = None
    project_id: int = 0
    name: str = ""
    description: str = ""
    completed: bool = False
    due_date: Optional[datetime] = None
    priority: str = "medium"  # low, medium, high, urgent
    tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Set default timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    @property
    def is_overdue(self) -> bool:
        """Check if the task is overdue."""
        if self.due_date and not self.completed:
            return datetime.now() > self.due_date
        return False

    @property
    def days_remaining(self) -> Optional[int]:
        """Calculate days remaining until due date."""
        if self.due_date:
            delta = self.due_date - datetime.now()
            return max(0, delta.days)
        return None

    @property
    def priority_color(self) -> str:
        """Get color code for priority level."""
        colors = {
            "low": "#28a745",  # Green
            "medium": "#ffc107",  # Yellow
            "high": "#fd7e14",  # Orange
            "urgent": "#dc3545",  # Red
        }
        return colors.get(self.priority, "#6c757d")  # Default gray

    @property
    def status_color(self) -> str:
        """Get color code for task status."""
        if self.completed:
            return "#28a745"  # Green for completed
        elif self.is_overdue:
            return "#dc3545"  # Red for overdue
        else:
            return "#007bff"  # Blue for active
