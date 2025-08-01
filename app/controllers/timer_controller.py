"""
Timer controller for the Cando application.

This module manages timer functionality including start, stop, and tracking
of time spent on tasks with enhanced Pomodoro support.
"""

from datetime import datetime, timedelta
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
        self.paused_timer: Optional[Timer] = None  # Store paused timer state
        self.pause_start_time: Optional[datetime] = None  # When pause started
        self.total_pause_duration: float = 0.0  # Total pause duration for current timer

    def start_timer(
        self,
        task_id: int,
        timer_type: str = "stopwatch",
        duration: int = None,
        pomodoro_session_type: str = None,
        pomodoro_session_number: int = None,
        count_down: bool = True,
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
            f"TimerController.start_timer called with: timer_type={timer_type}, duration={duration}, pomodoro_session_type={pomodoro_session_type}, count_down={count_down}"
        )

        # Stop any currently active timer
        if self.active_timer_id:
            self.stop_timer()

        # Reset pause duration for new timer
        self.total_pause_duration = 0.0

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
        self._clear_active_timer_cache()  # Clear cache when starting new timer

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
        work_count_down: bool = True,
        short_break_count_down: bool = True,
        long_break_count_down: bool = True,
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
            f"TimerController.start_pomodoro_session called with: session_type={session_type}, work_duration={work_duration}, short_break_duration={short_break_duration}, long_break_duration={long_break_duration}, work_count_down={work_count_down}, short_break_count_down={short_break_count_down}, long_break_count_down={long_break_count_down}"
        )

        # Determine session duration, number, and count direction
        if session_type == "work":
            duration = work_duration * 60  # Convert to seconds
            self.pomodoro_session_count += 1
            session_number = self.pomodoro_session_count
            count_down = work_count_down
        elif session_type == "short_break":
            duration = short_break_duration * 60  # Convert to seconds
            # Break sessions use the same number as the work session they follow
            session_number = self.pomodoro_session_count
            count_down = short_break_count_down
        elif session_type == "long_break":
            duration = long_break_duration * 60  # Convert to seconds
            # Break sessions use the same number as the work session they follow
            session_number = self.pomodoro_session_count
            count_down = long_break_count_down
        else:
            raise ValueError(f"Invalid session type: {session_type}")

        print(
            f"Calculated duration: {duration} seconds for session type: {session_type}, count_down: {count_down}"
        )

        return self.start_timer(
            task_id=task_id,
            timer_type="pomodoro",
            duration=duration,
            pomodoro_session_type=session_type,
            pomodoro_session_number=session_number,
            count_down=count_down,
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

        # Store the actual end time (when the timer was actually stopped)
        actual_end_time = datetime.now()

        # Calculate the effective duration (excluding pause time)
        effective_duration = None
        if self.total_pause_duration > 0:
            # Calculate effective duration by subtracting pause time from raw duration
            raw_duration = (
                actual_end_time - self.get_active_timer().start
            ).total_seconds()
            effective_duration = int(raw_duration - self.total_pause_duration)

        # Update timer in database with actual end time and effective duration
        db_timer = self.db_service.update_timer(
            timer_id=self.active_timer_id,
            end=actual_end_time,
            duration=effective_duration,
        )

        # Update cached timer to avoid database queries
        self._update_cached_timer_end_time(actual_end_time)

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
            # Reset pause tracking
            self.paused_timer = None
            self.pause_start_time = None
            self.total_pause_duration = 0.0
            self._clear_active_timer_cache()  # Clear cache when stopping timer
            return finished_timer

        return None

    def pause_timer(self) -> Optional[Timer]:
        """
        Pause the currently active timer.

        Returns:
            The paused timer object, or None if no active timer
        """
        if not self.active_timer_id:
            return None

        # Get the current timer
        active_timer = self.get_active_timer()
        if not active_timer:
            return None

        # Store the paused timer state
        self.paused_timer = active_timer
        self.pause_start_time = datetime.now()

        # Don't clear the active timer ID - keep it active but paused
        # This allows the display to continue showing the paused time

        return active_timer

    def resume_timer(self) -> Optional[Timer]:
        """
        Resume a paused timer.

        Returns:
            The resumed timer object, or None if no paused timer
        """
        if not self.paused_timer:
            return None

        # Calculate the pause duration and add it to total pause duration
        if self.pause_start_time:
            pause_duration = (datetime.now() - self.pause_start_time).total_seconds()
            self.total_pause_duration += pause_duration

        # Clear paused state
        self.paused_timer = None
        self.pause_start_time = None

        # Get the current timer (no changes needed to database)
        return self.get_active_timer()

    def skip_pomodoro_session(
        self,
        work_duration: int = 25,
        short_break_duration: int = 5,
        long_break_duration: int = 15,
        work_count_down: bool = True,
        short_break_count_down: bool = True,
        long_break_count_down: bool = True,
    ) -> Optional[Timer]:
        """
        Skip the current Pomodoro session and move to the next one.

        Args:
            work_duration: Work session duration in minutes
            short_break_duration: Short break duration in minutes
            long_break_duration: Long break duration in minutes
            work_count_down: Whether work sessions count down
            short_break_count_down: Whether short breaks count down
            long_break_count_down: Whether long breaks count down

        Returns:
            The completed timer object, or None if no active timer
        """
        if not self.active_timer_id:
            return None

        # Stop the current timer (mark it as completed)
        completed_timer = self.stop_timer()

        if completed_timer and completed_timer.type == "pomodoro":
            # Determine next session type based on what we just completed
            if completed_timer.pomodoro_session_type == "work":
                # Just completed a work session, so next should be a break
                next_session_type = self.get_next_pomodoro_session_type()
            elif completed_timer.pomodoro_session_type in ["short_break", "long_break"]:
                # Just completed a break session, so next should be a work session
                # Don't increment count here - it will be incremented when starting the work session
                next_session_type = "work"
            else:
                # Fallback
                next_session_type = self.get_next_pomodoro_session_type()

            # Start the next session
            return self.start_pomodoro_session(
                task_id=completed_timer.task_id,
                session_type=next_session_type,
                work_duration=work_duration,
                short_break_duration=short_break_duration,
                long_break_duration=long_break_duration,
                work_count_down=work_count_down,
                short_break_count_down=short_break_count_down,
                long_break_count_down=long_break_count_down,
            )

        return completed_timer

    def reset_pomodoro_cycle(self) -> None:
        """
        Reset the Pomodoro cycle to the first work session.
        """
        self.pomodoro_session_count = 0
        if self.active_timer_id:
            self.stop_timer()

    def is_timer_paused(self) -> bool:
        """
        Check if there's a paused timer.

        Returns:
            True if there's a paused timer, False otherwise
        """
        return self.paused_timer is not None

    def get_elapsed_at_pause(self) -> float:
        """
        Get the elapsed time at the moment the timer was paused.

        Returns:
            Elapsed time in seconds at pause, or 0 if not paused
        """
        if not self.paused_timer or not self.pause_start_time:
            return 0.0

        # Calculate the raw elapsed time at pause
        raw_elapsed_at_pause = (
            self.pause_start_time - self.paused_timer.start
        ).total_seconds()

        # Calculate the pause duration that occurred before this pause
        previous_pause_duration = self.total_pause_duration

        # Return the effective elapsed time at pause (excluding previous pauses)
        effective_elapsed_at_pause = raw_elapsed_at_pause - previous_pause_duration

        return max(0.0, effective_elapsed_at_pause)

    def get_effective_elapsed_time(self, timer: Timer) -> float:
        """
        Get the effective elapsed time for a timer, accounting for pauses.

        Args:
            timer: The timer object

        Returns:
            Effective elapsed time in seconds (excluding pause time)
        """
        if not timer:
            return 0.0

        # Calculate raw elapsed time
        if timer.end:
            raw_elapsed = (timer.end - timer.start).total_seconds()
        else:
            raw_elapsed = (datetime.now() - timer.start).total_seconds()

        # Subtract total pause duration
        effective_elapsed = raw_elapsed - self.total_pause_duration

        # Ensure we don't return negative time
        return max(0.0, effective_elapsed)

    def _update_cached_timer_end_time(self, end_time: datetime):
        """Update the cached timer's end time to avoid database queries."""
        if hasattr(self, "_cached_active_timer") and self._cached_active_timer:
            self._cached_active_timer.end = end_time

    def get_active_timer(self) -> Optional[Timer]:
        """
        Get the currently active timer.

        Returns:
            The active timer object, or None if no active timer
        """
        if not self.active_timer_id:
            return None

        # Cache the active timer to avoid database queries on every update
        if (
            not hasattr(self, "_cached_active_timer")
            or self._cached_active_timer is None
        ):
            db_timer = self.db_service.get_timers()
            active_timer = next(
                (t for t in db_timer if t.id == self.active_timer_id), None
            )

            if active_timer:
                self._cached_active_timer = Timer(
                    id=active_timer.id,
                    task_id=active_timer.task_id,
                    start=active_timer.start,
                    end=active_timer.end,
                    type=active_timer.type,
                    duration=active_timer.duration,
                    pomodoro_session_type=active_timer.pomodoro_session_type,
                    pomodoro_session_number=active_timer.pomodoro_session_number,
                )
            else:
                self._cached_active_timer = None

        return self._cached_active_timer

    def _clear_active_timer_cache(self):
        """Clear the cached active timer."""
        if hasattr(self, "_cached_active_timer"):
            self._cached_active_timer = None

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
