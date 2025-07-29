"""
Timer model
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Timer:
    """
    Timer model
    """

    id: int
    task_id: int
    start: datetime
    end: datetime
    type: str  # 'maduro', 'countdown', 'stopwatch'
