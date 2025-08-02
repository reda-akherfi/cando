"""
Habit model for the Cando application.

This module defines the Habit dataclass that represents a habit
in the productivity application with various tracking types.
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import List, Optional, Union
from enum import Enum


class HabitType(Enum):
    """Enumeration for different habit tracking types."""

    DURATION = "duration"  # Stopwatch-based (e.g., workout time)
    UNITS = "units"  # Integer-based (e.g., daily steps)
    REAL_NUMBER = "real_number"  # Float-based (e.g., weight)
    BOOLEAN = "boolean"  # Yes/No (e.g., did you meditate today?)
    RATING = "rating"  # 1-10 scale (e.g., mood rating)
    COUNT = "count"  # Simple counter (e.g., glasses of water)


class HabitFrequency(Enum):
    """Enumeration for habit frequency."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"  # Custom interval in days


@dataclass
class HabitEntry:
    """
    Individual habit entry/record.

    Represents a single tracking entry for a habit.
    """

    id: int
    habit_id: int
    date: date
    value: Union[float, int, bool, str]  # The tracked value
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Habit:
    """
    Habit model for tracking various types of habits.

    Supports different quantification methods:
    - Duration: Time-based tracking (e.g., workout duration)
    - Units: Integer-based tracking (e.g., daily steps)
    - Real Number: Float-based tracking (e.g., weight)
    - Boolean: Yes/No tracking (e.g., did you meditate?)
    - Rating: 1-10 scale tracking (e.g., mood)
    - Count: Simple counter (e.g., glasses of water)
    """

    id: int
    name: str
    description: Optional[str] = None
    habit_type: HabitType = HabitType.BOOLEAN
    frequency: HabitFrequency = HabitFrequency.DAILY
    custom_interval_days: Optional[int] = None  # For custom frequency
    target_value: Optional[Union[float, int]] = None  # Target goal
    unit: Optional[str] = None  # Unit of measurement (e.g., "steps", "minutes", "kg")
    color: str = "#007bff"  # Hex color for UI
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Optional fields for different habit types
    min_value: Optional[Union[float, int]] = None  # Minimum acceptable value
    max_value: Optional[Union[float, int]] = None  # Maximum acceptable value
    rating_scale: int = 10  # For rating type habits (1-10 by default)

    # Tags for categorization
    tags: List[str] = field(default_factory=list)

    # Recent entries (not persisted, loaded on demand)
    recent_entries: List[HabitEntry] = field(default_factory=list)

    def get_display_value(self, value: Union[float, int, bool, str]) -> str:
        """Get a formatted display value for the habit entry."""
        if self.habit_type == HabitType.DURATION:
            # Convert seconds to HH:MM:SS format
            hours = int(value // 3600)
            minutes = int((value % 3600) // 60)
            seconds = int(value % 60)
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes:02d}:{seconds:02d}"
        elif self.habit_type == HabitType.BOOLEAN:
            return "✓" if value else "✗"
        elif self.habit_type == HabitType.RATING:
            return f"{value}/10"
        else:
            unit_str = f" {self.unit}" if self.unit else ""
            return f"{value}{unit_str}"

    def is_completed_today(self) -> bool:
        """Check if the habit is completed for today."""
        today_value = self.get_today_value()
        if today_value is None:
            return False

        if self.habit_type == HabitType.BOOLEAN:
            return bool(today_value)
        elif self.target_value is not None:
            return today_value >= self.target_value
        else:
            return True  # Any entry counts as completion

    def get_today_value(self) -> Optional[Union[float, int, bool, str]]:
        """Get today's value for this habit."""
        today = date.today()
        today_entries = [entry for entry in self.recent_entries if entry.date == today]

        if not today_entries:
            return None

        if self.habit_type == HabitType.BOOLEAN:
            # For boolean habits, return True if any entry is True
            return any(bool(entry.value) for entry in today_entries)
        elif self.habit_type == HabitType.RATING:
            # For rating habits, return the average rating
            total_rating = sum(float(entry.value) for entry in today_entries)
            return total_rating / len(today_entries)
        else:
            # For numeric habits (duration, units, real_number, count), sum all values
            total_value = sum(float(entry.value) for entry in today_entries)
            # Return as int for integer types, float for others
            if self.habit_type in [HabitType.UNITS, HabitType.COUNT]:
                return int(total_value)
            else:
                return total_value

    def get_streak_days(self) -> int:
        """Calculate current streak of completed days."""
        streak = 0
        current_date = date.today()

        # Sort entries by date in descending order
        sorted_entries = sorted(self.recent_entries, key=lambda x: x.date, reverse=True)

        for entry in sorted_entries:
            if entry.date <= current_date:
                if self.habit_type == HabitType.BOOLEAN:
                    if not bool(entry.value):
                        break
                elif self.target_value is not None:
                    if entry.value < self.target_value:
                        break
                else:
                    # Any entry counts as completion
                    pass
                streak += 1
                current_date = entry.date - timedelta(days=1)
            else:
                break

        return streak
