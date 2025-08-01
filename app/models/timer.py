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
    type: str  # 'pomodoro', 'countdown', 'stopwatch'
    duration: int = None  # Duration in seconds for countdown/pomodoro
    pomodoro_session_type: str = None  # work, short_break, long_break
    pomodoro_session_number: int = None  # Session number in the cycle
