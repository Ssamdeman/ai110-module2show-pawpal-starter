from __future__ import annotations
from enum import Enum
from datetime import time


class Priority(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class Species(Enum):
    DOG = "dog"
    CAT = "cat"
    OTHER = "other"


class Owner:
    def __init__(self, name: str, day_start: time, day_end: time) -> None:
        self.name = name
        self.day_start = day_start
        self.day_end = day_end

    def available_minutes(self) -> int:
        pass


class Pet:
    def __init__(self, name: str, species: Species) -> None:
        self.name = name
        self.species = species


class Task:
    def __init__(self, title: str, duration_minutes: int, priority: Priority) -> None:
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority


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
        total_minutes_scheduled: int,
    ) -> None:
        self.scheduled = scheduled
        self.skipped = skipped
        self.total_minutes_available = total_minutes_available
        self.total_minutes_scheduled = total_minutes_scheduled

    def summary(self) -> str:
        pass


class Scheduler:
    def __init__(self, owner: Owner, tasks: list[Task]) -> None:
        self.owner = owner
        self.tasks = tasks

    def generate(self) -> Schedule:
        pass
