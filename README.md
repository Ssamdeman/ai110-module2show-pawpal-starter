# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Smarter Scheduling

Module 2 extended the core scheduler with four algorithmic improvements:

### Sort by time
`Scheduler.sort_by_time()` returns a pet's tasks ordered by `preferred_time`
(earliest first). Tasks with no time preference are pushed to the end using a
sentinel value (`24 * 60` minutes). The original task list is never mutated.

### Filter by status or pet name
`Scheduler.filter_tasks(completed=..., pet_name=...)` narrows a task list without
touching the underlying data. Pass `completed=True` for done tasks, `completed=False`
for pending, or a `pet_name` string to gate on the scheduler's assigned pet.

### Recurring task automation
Tasks carry a `recurrence` field (`DAILY` or `WEEKLY`) and a `due_date`.
Calling `Scheduler.mark_task_complete(task)` marks the task done **and**
automatically appends a fresh copy to `pet.tasks` with the next due date
calculated via Python's `timedelta` (`+1 day` for daily, `+7 days` for weekly).
Completed tasks are kept as a history record; `generate()` only schedules
pending tasks.

### Conflict detection
Two methods guard against scheduling collisions:

- `Scheduler.check_conflicts(schedule)` — scans one pet's schedule for
  overlapping time slots using a pairwise interval test
  (`a_start < b_end and b_start < a_end`). Returns warning strings; never raises.
- `Scheduler.cross_pet_conflicts(pairs)` — checks whether tasks from **different**
  pets overlap in time, catching cases where one person or sitter cannot
  physically handle both pets at once.

Both methods use `itertools.combinations` to generate unique slot pairs cleanly.

---

## Testing PawPal+

Run all tests with:

```bash
python -m pytest tests/test_pawpal.py -v
```

### What the tests cover

| Area | Tests |
|---|---|
| **Sorting** | Tasks return in chronological order; `None` preferred_time always goes last; priority beats time when both are set |
| **Recurrence** | Daily task spawns a new task due the next day; `pet.tasks` grows by 1; non-recurring tasks return `None` |
| **Conflict detection** | Overlapping slots produce a warning; back-to-back slots do not; empty schedule returns no warnings |
| **Core behavior** | Marking a task complete flips `completed`; adding tasks increases task count |

### Confidence level

⭐⭐⭐⭐ 4/5 — the core logic is solid and all 11 tests pass, but no system is perfect. Areas like cross-pet scheduling and greedy edge cases could use more coverage.

---

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
