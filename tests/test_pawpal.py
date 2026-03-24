import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, time, timedelta
from pawpal_system import (
    Task, Pet, Owner, Priority, Species, RecurrenceType,
    Scheduler, Schedule, ScheduledTask,
)


def test_mark_complete_changes_status():
    task = Task(title="Morning walk", duration_minutes=30, priority=Priority.HIGH)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species=Species.DOG)
    assert len(pet.tasks) == 0
    pet.tasks.append(Task(title="Feeding", duration_minutes=10, priority=Priority.HIGH))
    assert len(pet.tasks) == 1
    pet.tasks.append(Task(title="Walk", duration_minutes=20, priority=Priority.MEDIUM))
    assert len(pet.tasks) == 2


# ---------------------------------------------------------------------------
# Sorting Correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_chronological_order():
    """Tasks with preferred_time should be returned earliest-first."""
    pet = Pet(name="Mochi", species=Species.DOG)
    pet.tasks = [
        Task("Evening meds",  duration_minutes=5,  priority=Priority.LOW,    preferred_time=time(20, 0)),
        Task("Morning walk",  duration_minutes=30, priority=Priority.HIGH,   preferred_time=time(7, 0)),
        Task("Afternoon play",duration_minutes=20, priority=Priority.MEDIUM, preferred_time=time(14, 0)),
    ]
    owner = Owner("Sam", pet, day_start=time(6, 0), day_end=time(22, 0))
    scheduler = Scheduler(owner)

    sorted_tasks = scheduler.sort_by_time()
    times = [t.preferred_time for t in sorted_tasks]

    assert times == [time(7, 0), time(14, 0), time(20, 0)]


def test_sort_by_time_none_goes_last():
    """Tasks without a preferred_time should be pushed to the end."""
    pet = Pet(name="Mochi", species=Species.DOG)
    pet.tasks = [
        Task("No-preference task", duration_minutes=10, priority=Priority.HIGH, preferred_time=None),
        Task("Morning walk",       duration_minutes=30, priority=Priority.HIGH, preferred_time=time(7, 0)),
    ]
    owner = Owner("Sam", pet, day_start=time(6, 0), day_end=time(22, 0))
    scheduler = Scheduler(owner)

    sorted_tasks = scheduler.sort_by_time()

    assert sorted_tasks[0].title == "Morning walk"
    assert sorted_tasks[1].preferred_time is None


def test_generate_respects_priority_over_preferred_time():
    """A LOW-priority task at 06:00 should be scheduled AFTER a HIGH-priority task at 23:00."""
    pet = Pet(name="Mochi", species=Species.DOG)
    pet.tasks = [
        Task("Early LOW task", duration_minutes=10, priority=Priority.LOW,  preferred_time=time(6, 0)),
        Task("Late HIGH task", duration_minutes=10, priority=Priority.HIGH, preferred_time=time(23, 0)),
    ]
    owner = Owner("Sam", pet, day_start=time(6, 0), day_end=time(22, 0))
    scheduler = Scheduler(owner)

    schedule = scheduler.generate()
    titles = [st.task.title for st in schedule.scheduled]

    assert titles[0] == "Late HIGH task"
    assert titles[1] == "Early LOW task"


# ---------------------------------------------------------------------------
# Recurrence Logic
# ---------------------------------------------------------------------------

def test_daily_task_spawns_next_day():
    """Completing a DAILY task should create a new task due the following day."""
    today = date.today()
    task = Task(
        title="Feed Mochi",
        duration_minutes=10,
        priority=Priority.HIGH,
        recurrence=RecurrenceType.DAILY,
        due_date=today,
    )
    next_task = task.spawn_next()

    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.completed is False
    assert next_task.title == task.title


def test_mark_task_complete_appends_recurring_task():
    """mark_task_complete on a DAILY task should append a new task to pet.tasks."""
    today = date.today()
    task = Task(
        title="Feed Mochi",
        duration_minutes=10,
        priority=Priority.HIGH,
        recurrence=RecurrenceType.DAILY,
        due_date=today,
    )
    pet = Pet(name="Mochi", species=Species.DOG, tasks=[task])
    owner = Owner("Sam", pet, day_start=time(6, 0), day_end=time(22, 0))
    scheduler = Scheduler(owner)

    scheduler.mark_task_complete(task)

    assert len(pet.tasks) == 2                          # original + spawned
    assert pet.tasks[0].completed is True               # original is done
    assert pet.tasks[1].due_date == today + timedelta(days=1)  # spawned is tomorrow


def test_none_recurring_task_does_not_spawn():
    """A non-recurring task should return None from spawn_next."""
    task = Task(title="One-off bath", duration_minutes=20, priority=Priority.LOW,
                recurrence=RecurrenceType.NONE)
    result = task.spawn_next()

    assert result is None


# ---------------------------------------------------------------------------
# Conflict Detection
# ---------------------------------------------------------------------------

def test_check_conflicts_flags_overlapping_slots():
    """Two overlapping ScheduledTasks should produce a conflict warning."""
    pet = Pet(name="Mochi", species=Species.DOG)
    owner = Owner("Sam", pet, day_start=time(6, 0), day_end=time(22, 0))
    scheduler = Scheduler(owner)

    task_a = Task("Walk",    duration_minutes=30, priority=Priority.HIGH)
    task_b = Task("Feeding", duration_minutes=20, priority=Priority.MEDIUM)

    # Deliberately overlapping: 08:00–08:30 and 08:15–08:35
    slot_a = ScheduledTask(task_a, start_time=time(8, 0),  end_time=time(8, 30))
    slot_b = ScheduledTask(task_b, start_time=time(8, 15), end_time=time(8, 35))

    schedule = Schedule(scheduled=[slot_a, slot_b], skipped=[], total_minutes_available=960)
    warnings = scheduler.check_conflicts(schedule)

    assert len(warnings) == 1
    assert "WARNING" in warnings[0]
    assert "Walk" in warnings[0]
    assert "Feeding" in warnings[0]


def test_check_conflicts_no_warning_for_adjacent_slots():
    """Adjacent (back-to-back) slots should NOT be flagged as a conflict."""
    pet = Pet(name="Mochi", species=Species.DOG)
    owner = Owner("Sam", pet, day_start=time(6, 0), day_end=time(22, 0))
    scheduler = Scheduler(owner)

    task_a = Task("Walk",    duration_minutes=30, priority=Priority.HIGH)
    task_b = Task("Feeding", duration_minutes=20, priority=Priority.MEDIUM)

    # Adjacent: 08:00–08:30 then 08:30–08:50 — no overlap
    slot_a = ScheduledTask(task_a, start_time=time(8, 0),  end_time=time(8, 30))
    slot_b = ScheduledTask(task_b, start_time=time(8, 30), end_time=time(8, 50))

    schedule = Schedule(scheduled=[slot_a, slot_b], skipped=[], total_minutes_available=960)
    warnings = scheduler.check_conflicts(schedule)

    assert warnings == []


def test_check_conflicts_empty_schedule_returns_no_warnings():
    """An empty schedule should never raise and should return no warnings."""
    pet = Pet(name="Mochi", species=Species.DOG)
    owner = Owner("Sam", pet, day_start=time(6, 0), day_end=time(22, 0))
    scheduler = Scheduler(owner)

    schedule = Schedule(scheduled=[], skipped=[], total_minutes_available=960)
    warnings = scheduler.check_conflicts(schedule)

    assert warnings == []
