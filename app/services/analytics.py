"""
Analytics service for the Cando application.

This module provides data analysis and statistics for productivity insights
and visualization components.
"""

from datetime import datetime, timedelta
from typing import List, Dict
from app.models.project import Project
from app.models.task import Task
from app.models.timer import Timer
from app.models.tag import Tag
from app.services.database import DatabaseService
from app.services.adapters import (
    convert_project_list,
    convert_task_list,
    convert_tag_list,
    convert_timer_list,
)


class AnalyticsService:
    """
    Service for analyzing productivity data and generating insights.

    Provides methods to calculate time spent on projects, tasks, and tags,
    as well as productivity trends and statistics.
    """

    def __init__(self, db_service: DatabaseService):
        """
        Initialize the analytics service.

        Args:
            db_service: Database service instance for data access
        """
        self.db_service = db_service

    def get_time_by_project(self) -> Dict[str, float]:
        """
        Calculate total time spent on each project.

        Returns:
            Dictionary mapping project names to total hours spent
        """
        project_times = {}

        # Get all projects from database
        db_projects = self.db_service.get_projects()

        for db_project in db_projects:
            total_hours = 0

            # Get all tasks for this project
            project_tasks = self.db_service.get_tasks(project_id=db_project.id)

            for task in project_tasks:
                # Get all timers for this task
                task_timers = self.db_service.get_timers(task_id=task.id)

                for timer in task_timers:
                    if timer.end:
                        duration = timer.end - timer.start
                        total_hours += duration.total_seconds() / 3600

            project_times[db_project.name] = total_hours

        return project_times

    def get_time_by_tag(self) -> Dict[str, float]:
        """
        Calculate total time spent on each tag.

        Returns:
            Dictionary mapping tag names to total hours spent
        """
        tag_times = {}

        # Get all tags from database
        db_tags = self.db_service.get_tags()

        for db_tag in db_tags:
            total_hours = 0

            if db_tag.linked_type == "task":
                # Get all timers for this task
                task_timers = self.db_service.get_timers(task_id=db_tag.linked_id)

                for timer in task_timers:
                    if timer.end:
                        duration = timer.end - timer.start
                        total_hours += duration.total_seconds() / 3600

            tag_times[db_tag.name] = total_hours

        return tag_times

    def get_daily_productivity(self, days: int = 7) -> Dict[str, float]:
        """
        Calculate daily productivity for the last N days.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary mapping dates to total hours worked
        """
        daily_hours = {}
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        for i in range(days):
            current_date = start_date + timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")

            # Get all timers for this date
            all_timers = self.db_service.get_timers()
            day_timers = [
                timer
                for timer in all_timers
                if timer.start.date() == current_date.date() and timer.end
            ]

            total_hours = sum(
                (timer.end - timer.start).total_seconds() / 3600 for timer in day_timers
            )

            daily_hours[date_str] = total_hours

        return daily_hours

    def get_timer_type_stats(self) -> Dict[str, int]:
        """
        Get statistics on timer type usage.

        Returns:
            Dictionary mapping timer types to usage count
        """
        type_counts = {}

        # Get all timers from database
        all_timers = self.db_service.get_timers()

        for timer in all_timers:
            timer_type = timer.type
            type_counts[timer_type] = type_counts.get(timer_type, 0) + 1

        return type_counts

    def get_all_data(self) -> tuple[List[Project], List[Task], List[Timer], List[Tag]]:
        """
        Get all data from database as dataclass objects.

        Returns:
            Tuple of (projects, tasks, timers, tags) as dataclass lists
        """
        db_projects = self.db_service.get_projects()
        db_tasks = self.db_service.get_tasks()
        db_timers = self.db_service.get_timers()
        db_tags = self.db_service.get_tags()

        projects = convert_project_list(db_projects)
        tasks = convert_task_list(db_tasks)
        timers = convert_timer_list(db_timers)
        tags = convert_tag_list(db_tags)

        return projects, tasks, timers, tags

    def get_cumulative_work_data(self, days: int = 30) -> Dict[str, float]:
        """
        Calculate cumulative work hours over time, excluding break timers.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary mapping dates to cumulative hours worked (excluding breaks)
        """
        cumulative_hours = {}
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Get all timers
        all_timers = self.db_service.get_timers()

        # Filter out break timers and incomplete timers
        work_timers = [
            timer
            for timer in all_timers
            if timer.end
            and timer.start >= start_date
            and (
                timer.type != "pomodoro"
                or (timer.type == "pomodoro" and timer.pomodoro_session_type == "work")
            )
        ]

        # Sort by start date
        work_timers.sort(key=lambda x: x.start)

        # Calculate cumulative hours
        total_hours = 0
        current_date = start_date

        for i in range(days):
            current_date = start_date + timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")

            # Add hours for timers that ended on this date
            day_timers = [
                timer
                for timer in work_timers
                if timer.end.date() == current_date.date()
            ]

            day_hours = sum(
                (timer.end - timer.start).total_seconds() / 3600 for timer in day_timers
            )

            total_hours += day_hours
            cumulative_hours[date_str] = total_hours

        return cumulative_hours

    def get_tag_distribution(self) -> Dict[str, float]:
        """
        Calculate time distribution by tags, excluding break timers.

        Returns:
            Dictionary mapping tag names to total hours worked
        """
        tag_times = {}

        # Get all timers, excluding break timers
        all_timers = self.db_service.get_timers()
        work_timers = [
            timer
            for timer in all_timers
            if timer.end
            and (
                timer.type != "pomodoro"
                or (timer.type == "pomodoro" and timer.pomodoro_session_type == "work")
            )
        ]

        # Get all tasks with their tags
        all_tasks = self.db_service.get_tasks()
        task_tags = {}

        for task in all_tasks:
            if task.tags:
                task_tags[task.id] = [tag["name"] for tag in task.tags]

        # Calculate time per tag
        for timer in work_timers:
            timer_hours = (timer.end - timer.start).total_seconds() / 3600

            if timer.task_id in task_tags and task_tags[timer.task_id]:
                # Distribute time across all tags for this task
                tags = task_tags[timer.task_id]
                hours_per_tag = timer_hours / len(tags)
                for tag_name in tags:
                    tag_times[tag_name] = tag_times.get(tag_name, 0) + hours_per_tag
            else:
                # Task has no tags, add to "Untagged" category
                tag_times["Untagged"] = tag_times.get("Untagged", 0) + timer_hours

        return tag_times

    def get_project_distribution(self) -> Dict[str, float]:
        """
        Calculate time distribution by projects, excluding break timers.

        Returns:
            Dictionary mapping project names to total hours worked
        """
        project_times = {}

        # Get all timers, excluding break timers
        all_timers = self.db_service.get_timers()
        work_timers = [
            timer
            for timer in all_timers
            if timer.end
            and (
                timer.type != "pomodoro"
                or (timer.type == "pomodoro" and timer.pomodoro_session_type == "work")
            )
        ]

        # Get all tasks with their project info
        all_tasks = self.db_service.get_tasks()
        all_projects = self.db_service.get_projects()

        # Create task to project mapping
        task_project = {}
        project_names = {p.id: p.name for p in all_projects}

        for task in all_tasks:
            task_project[task.id] = task.project_id

        # Calculate time per project
        for timer in work_timers:
            if timer.task_id in task_project:
                project_id = task_project[timer.task_id]
                project_name = project_names.get(project_id, f"Project {project_id}")

                timer_hours = (timer.end - timer.start).total_seconds() / 3600
                project_times[project_name] = (
                    project_times.get(project_name, 0) + timer_hours
                )

        return project_times
