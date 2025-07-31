"""
Timer controller for the Cando application.

This module manages timer functionality including start, stop, and tracking
of time spent on tasks with enhanced Pomodoro support.
"""

from datetime import datetime
from typing import Optional
from app.models.timer import Timer
from app.services.database import DatabaseService


class TimerController:
    """
    Controller for managing timer operations.

    Handles starting, stopping, and tracking timers with database persistence
    and enhanced Pomodoro session management.
    """

    def __init__(self, db_service: DatabaseService):
        """
        Initialize the timer controller.

        Args:
            db_service: Database service for timer persistence
        """
        self.db_service = db_service
        self.active_timer_id: Optional[int] = None
        self.pomodoro_session_count = 0  # Track completed work sessions
        self.autostart_enabled = True  # Auto-start next session

    def start_timer(
        self,
        task_id: int,
        timer_type: str = "stopwatch",
        duration: int = None,
        pomodoro_session_type: str = None,
        pomodoro_session_number: int = None,
    ) -> Timer:
        """
        Start a new timer for a task.

        Args:
            task_id: ID of the task to time
            timer_type: Type of timer ('pomodoro', 'countdown', 'stopwatch')
            duration: Duration in seconds for countdown/pomodoro
            pomodoro_session_type: Type of Pomodoro session ('work', 'short_break', 'long_break')
            pomodoro_session_number: Session number in the Pomodoro cycle

        Returns:
            The created timer object
        """
        print(
            f"TimerController.start_timer called with: timer_type={timer_type}, duration={duration}, pomodoro_session_type={pomodoro_session_type}"
        )

        # Stop any currently active timer
        if self.active_timer_id:
            self.stop_timer()

        # Create new timer in database
        start_time = datetime.now()
        db_timer = self.db_service.create_timer(
            task_id=task_id,
            start=start_time,
            type=timer_type,
            duration=duration,
            pomodoro_session_type=pomodoro_session_type,
            pomodoro_session_number=pomodoro_session_number,
        )

        self.active_timer_id = db_timer.id

        # Convert to dataclass for return
        return Timer(
            id=db_timer.id,
            task_id=db_timer.task_id,
            start=db_timer.start,
            end=db_timer.end,
            type=db_timer.type,
            duration=db_timer.duration,
            pomodoro_session_type=db_timer.pomodoro_session_type,
            pomodoro_session_number=db_timer.pomodoro_session_number,
        )

    def start_pomodoro_session(
        self,
        task_id: int,
        session_type: str = "work",
        work_duration: int = 25,
        short_break_duration: int = 5,
        long_break_duration: int = 15,
    ) -> Timer:
        """
        Start a Pomodoro session with proper session tracking.

        Args:
            task_id: ID of the task to time
            session_type: Type of session ('work', 'short_break', 'long_break')
            work_duration: Work session duration in minutes
            short_break_duration: Short break duration in minutes
            long_break_duration: Long break duration in minutes

        Returns:
            The created timer object
        """
        print(
            f"TimerController.start_pomodoro_session called with: session_type={session_type}, work_duration={work_duration}, short_break_duration={short_break_duration}, long_break_duration={long_break_duration}"
        )

        # Determine session duration and number
        if session_type == "work":
            duration = work_duration * 60  # Convert to seconds
            self.pomodoro_session_count += 1
            session_number = self.pomodoro_session_count
        elif session_type == "short_break":
            duration = short_break_duration * 60  # Convert to seconds
            session_number = self.pomodoro_session_count
        elif session_type == "long_break":
            duration = long_break_duration * 60  # Convert to seconds
            session_number = self.pomodoro_session_count
        else:
            raise ValueError(f"Invalid session type: {session_type}")

        print(
            f"Calculated duration: {duration} seconds for session type: {session_type}"
        )

        return self.start_timer(
            task_id=task_id,
            timer_type="pomodoro",
            duration=duration,
            pomodoro_session_type=session_type,
            pomodoro_session_number=session_number,
        )

    def get_next_pomodoro_session_type(self) -> str:
        """
        Determine the next session type based on completed sessions.

        Returns:
            Next session type ('work', 'short_break', 'long_break')
        """
        if self.pomodoro_session_count == 0:
            return "work"

        # After every 4 work sessions, take a long break
        if self.pomodoro_session_count % 4 == 0:
            return "long_break"
        else:
            return "short_break"

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
                duration=db_timer.duration,
                pomodoro_session_type=db_timer.pomodoro_session_type,
                pomodoro_session_number=db_timer.pomodoro_session_number,
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
                duration=active_timer.duration,
                pomodoro_session_type=active_timer.pomodoro_session_type,
                pomodoro_session_number=active_timer.pomodoro_session_number,
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
            Timer(
                id=t.id,
                task_id=t.task_id,
                start=t.start,
                end=t.end,
                type=t.type,
                duration=t.duration,
                pomodoro_session_type=t.pomodoro_session_type,
                pomodoro_session_number=t.pomodoro_session_number,
            )
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
            Timer(
                id=t.id,
                task_id=t.task_id,
                start=t.start,
                end=t.end,
                type=t.type,
                duration=t.duration,
                pomodoro_session_type=t.pomodoro_session_type,
                pomodoro_session_number=t.pomodoro_session_number,
            )
            for t in db_timers
        ]

    def get_pomodoro_stats(self, task_id: int = None) -> dict:
        """
        Get Pomodoro statistics for a task or all tasks.

        Args:
            task_id: Optional task ID to filter by

        Returns:
            Dictionary with Pomodoro statistics
        """
        timers = self.get_task_timers(task_id) if task_id else self.get_all_timers()
        pomodoro_timers = [t for t in timers if t.type == "pomodoro" and t.end]

        work_sessions = [
            t for t in pomodoro_timers if t.pomodoro_session_type == "work"
        ]
        short_breaks = [
            t for t in pomodoro_timers if t.pomodoro_session_type == "short_break"
        ]
        long_breaks = [
            t for t in pomodoro_timers if t.pomodoro_session_type == "long_break"
        ]

        total_work_time = sum((t.end - t.start).total_seconds() for t in work_sessions)
        total_break_time = sum(
            (t.end - t.start).total_seconds() for t in short_breaks + long_breaks
        )

        return {
            "total_work_sessions": len(work_sessions),
            "total_short_breaks": len(short_breaks),
            "total_long_breaks": len(long_breaks),
            "total_work_time": total_work_time,
            "total_break_time": total_break_time,
            "current_session_count": self.pomodoro_session_count,
        }
