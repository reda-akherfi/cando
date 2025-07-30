"""
Tag model
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Tag:
    """
    Tag entity representing a reusable tag.

    Tags can be attached to projects and tasks for categorization
    and organization purposes.
    """

    id: Optional[int] = None
    name: str = ""
    color: str = "#FF5733"  # Default color
    description: str = ""
    usage_count: int = 0
    linked_projects: List[int] = field(default_factory=list)
    linked_tasks: List[int] = field(default_factory=list)
