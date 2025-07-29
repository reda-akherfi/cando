"""
Tag model
"""

from dataclasses import dataclass


@dataclass
class Tag:
    """
    Tag model
    """

    id: int
    name: str
    linked_type: str  # 'project' or 'task'
    linked_id: int
