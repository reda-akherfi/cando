"""
Timer controller for the Cando application.

This module manages timer functionality including start, stop, and tracking
of time spent on tasks.
"""

from datetime import datetime
from typing import Optional
from app.models.timer import Timer
from app.services.database import DatabaseService


class TimerController:
    """
    Controller for managing timer operations.

    Handles starting, stopping, and tracking timers with database persistence.
    """

    def __init__(self, db_service: DatabaseService):
        """
        Initialize the timer controller.

        Args:
            db_service: Database service for timer persistence
        """
        self.db_service = db_service
        self.active_timer_id: Optional[int] = None

    def start_timer(self, task_id: int, timer_type: str = "stopwatch") -> Timer:
        """
        Start a new timer for a task.

        Args:
            task_id: ID of the task to time
            timer_type: Type of timer ('maduro', 'countdown', 'stopwatch')

        Returns:
            The created timer object
        """
        # Stop any currently active timer
        if self.active_timer_id:
            self.stop_timer()

        # Create new timer in database
        start_time = datetime.now()
        db_timer = self.db_service.create_timer(
            task_id=task_id, start=start_time, type=timer_type
        )

        self.active_timer_id = db_timer.id

        # Convert to dataclass for return
        return Timer(
            id=db_timer.id,
            task_id=db_timer.task_id,
            start=db_timer.start,
            end=db_timer.end,
            type=db_timer.type,
        )

    def stop_timer(self) -> Optional[Timer]:
        """
        Stop the currently active timer.

        Returns:
            The stopped timer object, or None if no active timer
        """
        if not self.active_timer_id:
            return None

        # Update timer in database
        end_time = datetime.now()
        db_timer = self.db_service.update_timer(
            timer_id=self.active_timer_id, end=end_time
        )

        if db_timer:
            # Convert to dataclass for return
            finished_timer = Timer(
                id=db_timer.id,
                task_id=db_timer.task_id,
                start=db_timer.start,
                end=db_timer.end,
                type=db_timer.type,
            )

            self.active_timer_id = None
            return finished_timer

        return None

    def get_active_timer(self) -> Optional[Timer]:
        """
        Get the currently active timer.

        Returns:
            The active timer object, or None if no active timer
        """
        if not self.active_timer_id:
            return None

        db_timer = self.db_service.get_timers()
        active_timer = next((t for t in db_timer if t.id == self.active_timer_id), None)

        if active_timer:
            return Timer(
                id=active_timer.id,
                task_id=active_timer.task_id,
                start=active_timer.start,
                end=active_timer.end,
                type=active_timer.type,
            )

        return None

    def get_task_timers(self, task_id: int) -> list[Timer]:
        """
        Get all timers for a specific task.

        Args:
            task_id: ID of the task

        Returns:
            List of timer objects for the task
        """
        db_timers = self.db_service.get_timers(task_id=task_id)
        return [
            Timer(id=t.id, task_id=t.task_id, start=t.start, end=t.end, type=t.type)
            for t in db_timers
        ]

    def get_all_timers(self) -> list[Timer]:
        """
        Get all timers from the database.

        Returns:
            List of all timer objects
        """
        db_timers = self.db_service.get_timers()
        return [
            Timer(id=t.id, task_id=t.task_id, start=t.start, end=t.end, type=t.type)
            for t in db_timers
        ]
