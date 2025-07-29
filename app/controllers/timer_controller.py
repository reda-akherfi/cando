# app/controllers/timer_controller.py
from datetime import datetime
from app.models.timer import Timer


class TimerController:
    def __init__(self):
        self.active_timer = None

    def start_timer(self, task_id: int, timer_type: str) -> Timer:
        self.active_timer = Timer(
            id=-1, task_id=task_id, start=datetime.now(), end=None, type=timer_type
        )
        return self.active_timer

    def stop_timer(self):
        if self.active_timer:
            self.active_timer.end = datetime.now()
            finished = self.active_timer
            self.active_timer = None
            return finished
        return None
