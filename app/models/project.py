"""
    Project model
"""

from dataclasses import dataclass, field

from typing import List


@dataclass
class Project:
    """
    Project model
    """

    id: int
    name: str
    description: str = ""
    tasks: List[int] = field(default_factory=list)
