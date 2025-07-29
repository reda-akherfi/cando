# app/models/timer.py
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Timer:
    id: int
    task_id: int
    start: datetime
    end: datetime
    type: str  # 'maduro', 'countdown', 'stopwatch'
