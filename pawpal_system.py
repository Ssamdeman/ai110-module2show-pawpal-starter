from __future__ import annotations
from enum import Enum
from datetime import datetime, time, timedelta


class Priority(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class Species(Enum):
    DOG = "dog"
    CAT = "cat"
    OTHER = "other"


class Owner:
    def __init__(self, name: str, pet: Pet, day_start: time, day_end: time) -> None:
        self.name = name
        self.pet = pet
        self.day_start = day_start
        self.day_end = day_end

    def available_minutes(self) -> int:
        """Return total minutes between day_start and day_end."""
        dummy = datetime(2000, 1, 1)
        delta = datetime.combine(dummy, self.day_end) - datetime.combine(dummy, self.day_start)
        return int(delta.total_seconds() // 60)


class Pet:
    def __init__(self, name: str, species: Species, tasks: list[Task] | None = None) -> None:
        self.name = name
        self.species = species
        self.tasks = tasks if tasks is not None else []


class Task:
    def __init__(self, title: str, duration_minutes: int, priority: Priority) -> None:
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.completed = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True


class ScheduledTask:
    def __init__(self, task: Task, start_time: time, end_time: time) -> None:
        self.task = task
        self.start_time = start_time
        self.end_time = end_time


class Schedule:
    def __init__(
        self,
        scheduled: list[ScheduledTask],
        skipped: list[Task],
        total_minutes_available: int,
    ) -> None:
        self.scheduled = scheduled
        self.skipped = skipped
        self.total_minutes_available = total_minutes_available
        self.total_minutes_scheduled = sum(st.task.duration_minutes for st in scheduled)

    def summary(self) -> str:
        """Return a human-readable summary of scheduled vs skipped tasks."""
        result = (
            f"Scheduled {self.total_minutes_scheduled} of "
            f"{self.total_minutes_available} minutes — "
            f"{len(self.scheduled)} task(s) planned."
        )
        if self.skipped:
            result += f" {len(self.skipped)} task(s) skipped due to insufficient time."
        return result


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def generate(self) -> Schedule:
        """Build a daily schedule by fitting tasks into the owner's time window, highest priority first."""
        available = self.owner.available_minutes()
        remaining = available

        sorted_tasks = sorted(self.owner.pet.tasks, key=lambda t: t.priority.value)

        scheduled: list[ScheduledTask] = []
        skipped: list[Task] = []

        dummy = datetime(2000, 1, 1)
        current_dt = datetime.combine(dummy, self.owner.day_start)

        for task in sorted_tasks:
            if task.duration_minutes <= remaining:
                end_dt = current_dt + timedelta(minutes=task.duration_minutes)
                scheduled.append(ScheduledTask(task, current_dt.time(), end_dt.time()))
                current_dt = end_dt
                remaining -= task.duration_minutes
            else:
                skipped.append(task)

        return Schedule(scheduled, skipped, available)
