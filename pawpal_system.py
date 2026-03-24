from __future__ import annotations
from enum import Enum
from datetime import datetime, time, timedelta, date
from itertools import combinations


class Priority(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class Species(Enum):
    DOG = "dog"
    CAT = "cat"
    OTHER = "other"


class RecurrenceType(Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"


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
    """A single pet-care activity with scheduling metadata.

    Attributes:
        title:            Human-readable name (e.g. "Morning walk").
        duration_minutes: How long the task takes in minutes.
        priority:         Priority.HIGH / MEDIUM / LOW — drives schedule order.
        preferred_time:   Optional ideal start time; used as a tiebreaker when
                          two tasks share the same priority.
        recurrence:       RecurrenceType.DAILY / WEEKLY / NONE — controls whether
                          completing the task auto-spawns a next occurrence.
        due_date:         Calendar date this instance is due; used by spawn_next()
                          to calculate the following occurrence's date via timedelta.
        completed:        Set to True by mark_complete(); completed tasks are
                          excluded from generate() but kept as a history record.
    """

    def __init__(
        self,
        title: str,
        duration_minutes: int,
        priority: Priority,
        preferred_time: time | None = None,
        recurrence: RecurrenceType = RecurrenceType.NONE,
        due_date: date | None = None,
    ) -> None:
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.preferred_time = preferred_time   # optional desired start time
        self.recurrence = recurrence
        self.due_date = due_date               # None means "today / unscheduled"
        self.completed = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def spawn_next(self) -> "Task | None":
        """Return a fresh Task for the next occurrence, or None if non-recurring.

        The new task is a clean copy (completed=False) whose due_date is
        calculated from today using timedelta:
          - DAILY  -> today + 1 day
          - WEEKLY -> today + 7 days

        The caller is responsible for appending the result to pet.tasks.
        """
        today = date.today()
        base  = self.due_date if self.due_date is not None else today

        if self.recurrence is RecurrenceType.DAILY:
            next_date = base + timedelta(days=1)
        elif self.recurrence is RecurrenceType.WEEKLY:
            next_date = base + timedelta(weeks=1)
        else:
            return None   # non-recurring — nothing to spawn

        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            preferred_time=self.preferred_time,
            recurrence=self.recurrence,
            due_date=next_date,
        )


class ScheduledTask:
    """A Task that has been placed on the timeline with concrete start/end times.

    Created exclusively by Scheduler.generate(); not constructed manually
    except when building test or conflict-demo schedules.
    """

    def __init__(self, task: Task, start_time: time, end_time: time) -> None:
        self.task = task
        self.start_time = start_time
        self.end_time = end_time


class Schedule:
    """The output of Scheduler.generate() — what fits, what was skipped, and why.

    Attributes:
        scheduled:               Ordered list of ScheduledTask objects that fit
                                 within the owner's time window.
        skipped:                 Tasks that could not be placed (insufficient
                                 remaining time when they were reached).
        total_minutes_available: Total minutes in the owner's day window.
        total_minutes_scheduled: Sum of durations of all placed tasks (derived
                                 automatically; never passed in by the caller).
    """

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

    def sort_by_time(self) -> list[Task]:
        """Return the pet's tasks sorted by preferred_time (earliest first).

        Tasks with no preferred_time are pushed to the end of the list.
        The original pet.tasks list is not mutated.

        Uses Python's sorted() with a key function that converts each
        preferred_time to minutes-since-midnight (an int), so the comparison
        is fast and readable.  None is replaced by the sentinel 24*60 (1440)
        so it always sorts after any real time value.
        """
        def time_key(t: Task) -> int:
            if t.preferred_time is not None:
                return t.preferred_time.hour * 60 + t.preferred_time.minute
            return 24 * 60   # sentinel — no preference goes last

        return sorted(self.owner.pet.tasks, key=time_key)

    def filter_tasks(
        self,
        *,
        completed: bool | None = None,
        pet_name: str | None = None,
    ) -> list[Task]:
        """Filter the pet's tasks by completion status and/or pet name.

        Args:
            completed:  True  -> only completed tasks
                        False -> only pending (not yet done) tasks
                        None  -> no status filter (return all)
            pet_name:   When provided, only return tasks if the owner's pet
                        name matches (case-insensitive).  Useful when this
                        Scheduler might serve different pets dynamically.

        Returns a new list; the original pet.tasks is never modified.
        """
        tasks = list(self.owner.pet.tasks)

        if pet_name is not None:
            if self.owner.pet.name.lower() != pet_name.lower():
                return []   # wrong pet — nothing matches

        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]

        return tasks

    def mark_task_complete(self, task: Task) -> "Task | None":
        """Mark a task done and, if it recurs, auto-create the next occurrence.

        Steps:
          1. Call task.mark_complete() to set task.completed = True.
          2. Call task.spawn_next() — uses timedelta to compute the next due_date.
          3. If a next task is returned, append it to pet.tasks so it will be
             picked up the next time generate() runs.

        Returns the newly spawned Task, or None for non-recurring tasks.
        """
        task.mark_complete()
        next_task = task.spawn_next()
        if next_task is not None:
            self.owner.pet.tasks.append(next_task)
        return next_task

    def check_conflicts(self, schedule: Schedule) -> list[str]:
        """Scan a schedule for overlapping time slots on the same pet.

        Strategy — pairwise interval overlap test:
          Two slots A and B overlap when A starts before B ends AND
          B starts before A ends:  a_start < b_end and b_start < a_end

        This is "lightweight" in two ways:
          1. Returns warning strings instead of raising exceptions, so the
             program keeps running and the caller decides what to do.
          2. Works on the already-built Schedule object, so it never needs
             to re-run the scheduling algorithm.

        Returns an empty list when there are no conflicts.
        """
        warnings: list[str] = []
        dummy = datetime(2000, 1, 1)

        # combinations(slots, 2) yields every unique (a, b) pair without
        # duplicates or self-pairs — cleaner than a manual index loop.
        for a, b in combinations(schedule.scheduled, 2):
            a_start = datetime.combine(dummy, a.start_time)
            a_end   = datetime.combine(dummy, a.end_time)
            b_start = datetime.combine(dummy, b.start_time)
            b_end   = datetime.combine(dummy, b.end_time)

            if a_start < b_end and b_start < a_end:
                warnings.append(
                    f"WARNING [{self.owner.pet.name}]: "
                    f"'{a.task.title}' ({a.start_time.strftime('%H:%M')}-{a.end_time.strftime('%H:%M')}) "
                    f"overlaps with "
                    f"'{b.task.title}' ({b.start_time.strftime('%H:%M')}-{b.end_time.strftime('%H:%M')})"
                )

        return warnings

    @staticmethod
    def cross_pet_conflicts(pairs: list[tuple[Owner, Schedule]]) -> list[str]:
        """Check whether tasks from DIFFERENT pets overlap in time.

        Real-world case: one person (or a pet sitter) is responsible for
        multiple pets.  If Mochi's walk runs 07:00-07:30 and Luna's litter
        clean runs 07:15-07:25, that person cannot physically do both at once.

        Strategy:
          Flatten all scheduled slots from every owner/pet into one list,
          tagging each slot with its owner+pet label.  Then do a pairwise
          overlap check, skipping pairs that share the same label (those are
          caught by check_conflicts instead).

        Returns warning strings — never raises an exception.
        """
        warnings: list[str] = []
        dummy = datetime(2000, 1, 1)

        # Build a flat list of (label, ScheduledTask) across all schedules
        labeled: list[tuple[str, ScheduledTask]] = []
        for owner, schedule in pairs:
            label = f"{owner.name}/{owner.pet.name}"
            for st in schedule.scheduled:
                labeled.append((label, st))

        # Pairwise check — only compare slots from DIFFERENT pets
        for (label_a, slot_a), (label_b, slot_b) in combinations(labeled, 2):
            if label_a == label_b:
                continue  # same pet — handled by check_conflicts

            a_start = datetime.combine(dummy, slot_a.start_time)
            a_end   = datetime.combine(dummy, slot_a.end_time)
            b_start = datetime.combine(dummy, slot_b.start_time)
            b_end   = datetime.combine(dummy, slot_b.end_time)

            if a_start < b_end and b_start < a_end:
                warnings.append(
                    f"WARNING [cross-pet]: "
                    f"{label_a} '{slot_a.task.title}' "
                    f"({slot_a.start_time.strftime('%H:%M')}-{slot_a.end_time.strftime('%H:%M')}) "
                    f"overlaps with "
                    f"{label_b} '{slot_b.task.title}' "
                    f"({slot_b.start_time.strftime('%H:%M')}-{slot_b.end_time.strftime('%H:%M')})"
                )

        return warnings

    def generate(self) -> Schedule:
        """Build a daily schedule fitting tasks into the owner's time window.

        Sorting logic:
          1. Primary key  — priority (HIGH before MEDIUM before LOW)
          2. Secondary key — preferred_time (earlier times first; None sorts last)
        """
        available = self.owner.available_minutes()
        remaining = available

        # Only schedule tasks that haven't been completed yet.
        # Completed recurring tasks stay in pet.tasks as a history record;
        # their spawned replacements (completed=False) are what get scheduled.
        pending_tasks = [t for t in self.owner.pet.tasks if not t.completed]

        def sort_key(t: Task):
            # Convert preferred_time to minutes-since-midnight so None can be
            # treated as a large sentinel (pushed to the end within its priority band).
            if t.preferred_time is not None:
                pt = t.preferred_time.hour * 60 + t.preferred_time.minute
            else:
                pt = 24 * 60  # sentinel: "no preference" goes last
            return (t.priority.value, pt)

        sorted_tasks = sorted(pending_tasks, key=sort_key)

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


# ---------------------------------------------------------------------------
# Algorithm helpers
# ---------------------------------------------------------------------------

def filter_tasks(tasks: list[Task], *, pet_name: str | None = None, completed: bool | None = None) -> list[Task]:
    """Filter a flat task list by pet name and/or completion status.

    Args:
        tasks:      Flat list of Task objects (already extracted from a Pet).
        pet_name:   When provided, only keep tasks whose owning pet matches
                    (pass the pet's name alongside its tasks — see usage in main.py).
        completed:  True → only completed tasks; False → only pending tasks;
                    None → no status filter.
    """
    result = tasks
    if completed is not None:
        result = [t for t in result if t.completed == completed]
    return result


def filter_tasks_by_pet(owners: list[Owner], pet_name: str) -> list[Task]:
    """Return all tasks belonging to the pet with the given name."""
    for owner in owners:
        if owner.pet.name.lower() == pet_name.lower():
            return list(owner.pet.tasks)
    return []


def detect_conflicts(schedules: list[tuple[Owner, Schedule]]) -> list[str]:
    """Detect scheduling conflicts across multiple owner-schedule pairs.

    Two conflict types are checked:
      1. Same pet double-booked — two owners share the same Pet object.
      2. Overlapping time slots within a single schedule (shouldn't happen with
         the sequential scheduler, but catches manually constructed schedules).

    Returns a list of human-readable conflict description strings.
    """
    conflicts: list[str] = []

    # --- conflict type 1: same pet assigned to multiple owners ---------------
    seen_pets: dict[str, str] = {}  # pet_name -> first owner name
    for owner, _ in schedules:
        pet_key = owner.pet.name.lower()
        if pet_key in seen_pets:
            conflicts.append(
                f"Conflict: '{owner.pet.name}' is assigned to both "
                f"'{seen_pets[pet_key]}' and '{owner.name}'."
            )
        else:
            seen_pets[pet_key] = owner.name

    # --- conflict type 2: overlapping slots within one schedule --------------
    dummy = datetime(2000, 1, 1)

    for owner, schedule in schedules:
        slots = schedule.scheduled
        for i in range(len(slots)):
            for j in range(i + 1, len(slots)):
                a_start = datetime.combine(dummy, slots[i].start_time)
                a_end   = datetime.combine(dummy, slots[i].end_time)
                b_start = datetime.combine(dummy, slots[j].start_time)
                b_end   = datetime.combine(dummy, slots[j].end_time)
                # Overlap when one interval starts before the other ends
                if a_start < b_end and b_start < a_end:
                    conflicts.append(
                        f"Overlap in {owner.name}'s schedule: "
                        f"'{slots[i].task.title}' ({slots[i].start_time.strftime('%H:%M')}–"
                        f"{slots[i].end_time.strftime('%H:%M')}) overlaps with "
                        f"'{slots[j].task.title}' ({slots[j].start_time.strftime('%H:%M')}–"
                        f"{slots[j].end_time.strftime('%H:%M')})."
                    )

    return conflicts
