"""
Project model for the Cando application.

This module defines the Project dataclass that represents a project
in the productivity application.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Project:
    """
    Project entity representing a work project.

    A project is a collection of related tasks that work towards
    a common goal or deliverable.
    """

    id: Optional[int] = None
    name: str = ""
    description: str = ""
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    priority: str = "medium"  # low, medium, high, urgent
    status: str = "active"  # active, completed, paused, cancelled
    tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        """Set default timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    @property
    def is_overdue(self) -> bool:
        """Check if the project is overdue."""
        if self.due_date and self.status != "completed":
            return datetime.now() > self.due_date
        return False

    @property
    def progress_percentage(self) -> float:
        """Calculate project progress based on completed tasks."""
        # This will be calculated by the service layer
        return 0.0

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
        """Get color code for status."""
        colors = {
            "active": "#007bff",  # Blue
            "completed": "#28a745",  # Green
            "paused": "#ffc107",  # Yellow
            "cancelled": "#dc3545",  # Red
        }
        return colors.get(self.status, "#6c757d")  # Default gray
