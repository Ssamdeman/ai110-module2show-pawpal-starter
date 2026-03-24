from datetime import time, date
from pawpal_system import (
    Owner, Pet, Task, Scheduler, Schedule, ScheduledTask,
    Priority, Species, RecurrenceType,
)

TODAY = date.today()


# ---------------------------------------------------------------------------
# Tasks added deliberately OUT OF TIME ORDER to prove sort_by_time() works
# ---------------------------------------------------------------------------
#   Mochi's tasks are given preferred_times scrambled: 8:30, 7:00, 9:00, 7:30
#   Luna's tasks mix times and None values

mochi = Pet(
    name="Mochi",
    species=Species.DOG,
    tasks=[
        Task("Grooming session", 45, Priority.MEDIUM, preferred_time=time(8, 30)),                                                    # 3rd
        Task("Morning walk",     30, Priority.HIGH,   preferred_time=time(7,  0), recurrence=RecurrenceType.DAILY,  due_date=TODAY),  # 1st
        Task("Enrichment play",  20, Priority.LOW,    preferred_time=time(9,  0)),                                                    # 4th
        Task("Feeding",          10, Priority.HIGH,   preferred_time=time(7, 30), recurrence=RecurrenceType.DAILY,  due_date=TODAY),  # 2nd
    ],
)

luna = Pet(
    name="Luna",
    species=Species.CAT,
    tasks=[
        Task("Vet call",         60, Priority.LOW),                                                                                          # no time -> last
        Task("Feeding",          10, Priority.HIGH,   preferred_time=time(8, 10), recurrence=RecurrenceType.DAILY,  due_date=TODAY),        # 2nd
        Task("Brushing",         20, Priority.LOW,    preferred_time=time(8, 45), recurrence=RecurrenceType.WEEKLY, due_date=TODAY),        # 4th
        Task("Litter box clean", 10, Priority.HIGH,   preferred_time=time(8,  0), recurrence=RecurrenceType.DAILY,  due_date=TODAY),        # 1st
        Task("Laser play",       15, Priority.MEDIUM, preferred_time=time(8, 30)),                                                          # 3rd
    ],
)

jordan = Owner(name="Jordan", pet=mochi, day_start=time(7, 0),  day_end=time(9, 0))
alex   = Owner(name="Alex",   pet=luna,  day_start=time(8, 0),  day_end=time(9, 30))

jordan_sched = Scheduler(owner=jordan)
alex_sched   = Scheduler(owner=alex)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def print_task_list(tasks: list, label: str) -> None:
    print(f"\n  {label}")
    print("  " + "-" * 44)
    if not tasks:
        print("    (none)")
        return
    for t in tasks:
        time_str = t.preferred_time.strftime("%H:%M") if t.preferred_time else "no pref"
        status   = "done" if t.completed else "pending"
        recur    = f" [{t.recurrence.value}]" if t.recurrence != RecurrenceType.NONE else ""
        print(f"    {time_str}  [{t.priority.name:<6}]  [{status}]  {t.title}{recur}")


def print_schedule(owner: Owner, schedule) -> None:
    print("=" * 50)
    print(f"Schedule — {owner.name} & {owner.pet.name} ({owner.pet.species.value})")
    print(f"Window : {owner.day_start.strftime('%H:%M')} - {owner.day_end.strftime('%H:%M')}")
    print("=" * 50)
    if not schedule.scheduled:
        print("  No tasks could be scheduled.")
    else:
        for st in schedule.scheduled:
            recur = f" [{st.task.recurrence.value}]" if st.task.recurrence != RecurrenceType.NONE else ""
            print(
                f"  {st.start_time.strftime('%H:%M')} - {st.end_time.strftime('%H:%M')}"
                f"  [{st.task.priority.name:<6}]  {st.task.title}{recur}"
            )
    if schedule.skipped:
        print("\n  [!] Skipped (not enough time):")
        for t in schedule.skipped:
            print(f"    - {t.title} ({t.duration_minutes} min)")
    print(f"\n  {schedule.summary()}\n")


# ---------------------------------------------------------------------------
# Section 1 — sort_by_time(): show tasks reordered by preferred_time
# ---------------------------------------------------------------------------

print("\n" + "#" * 50)
print("# SORT BY TIME")
print("#" * 50)

print("\nMochi's tasks as added (out of order):")
print_task_list(mochi.tasks, "original insertion order")

print("\nMochi's tasks after sort_by_time():")
print_task_list(jordan_sched.sort_by_time(), "sorted by preferred_time")

print("\nLuna's tasks as added (out of order):")
print_task_list(luna.tasks, "original insertion order")

print("\nLuna's tasks after sort_by_time():")
print_task_list(alex_sched.sort_by_time(), "sorted by preferred_time  (None -> last)")


# ---------------------------------------------------------------------------
# Section 2 — filter_tasks(): by status and by pet name
# ---------------------------------------------------------------------------

print("\n" + "#" * 50)
print("# FILTER BY STATUS")
print("#" * 50)

# Mark a couple of Mochi's tasks complete via the scheduler so recurring
# tasks automatically spawn their next occurrence.
jordan_sched.mark_task_complete(mochi.tasks[1])  # Morning walk (DAILY)
jordan_sched.mark_task_complete(mochi.tasks[3])  # Feeding      (DAILY)

print_task_list(jordan_sched.filter_tasks(completed=True),  "Mochi — completed tasks")
print_task_list(jordan_sched.filter_tasks(completed=False), "Mochi — pending tasks")

print("\n" + "#" * 50)
print("# FILTER BY PET NAME")
print("#" * 50)

print_task_list(alex_sched.filter_tasks(pet_name="Luna"),    "Alex's scheduler -> asking for 'Luna' (match)")
print_task_list(alex_sched.filter_tasks(pet_name="Mochi"),   "Alex's scheduler -> asking for 'Mochi' (no match)")
print_task_list(jordan_sched.filter_tasks(pet_name="Mochi"), "Jordan's scheduler -> asking for 'Mochi' (match)")


# ---------------------------------------------------------------------------
# Section 3 — Recurring task automation
# ---------------------------------------------------------------------------

print("\n" + "#" * 50)
print("# RECURRING TASK AUTOMATION")
print("#" * 50)

def print_recurring_demo(scheduler: Scheduler, label: str) -> None:
    print(f"\n  {label}")
    print("  " + "-" * 44)
    for t in scheduler.owner.pet.tasks:
        if t.recurrence == RecurrenceType.NONE:
            continue
        due_str    = str(t.due_date) if t.due_date else "no date"
        status_str = "DONE" if t.completed else "pending"
        print(
            f"    [{status_str:<7}]  due {due_str}"
            f"  [{t.recurrence.value:<6}]  {t.title}"
        )

# Before completing anything, show Luna's recurring tasks
print("\nLuna's recurring tasks BEFORE completing any:")
print_recurring_demo(alex_sched, "current state")

# Mark Luna's daily tasks complete via mark_task_complete()
completed_feeding = luna.tasks[1]          # Feeding (DAILY)
completed_litter  = luna.tasks[3]          # Litter box clean (DAILY)
completed_brush   = luna.tasks[2]          # Brushing (WEEKLY)

next_feeding = alex_sched.mark_task_complete(completed_feeding)
next_litter  = alex_sched.mark_task_complete(completed_litter)
next_brush   = alex_sched.mark_task_complete(completed_brush)

print(f"\n  mark_task_complete('Feeding')          -> spawned: '{next_feeding.title}' due {next_feeding.due_date}")
print(f"  mark_task_complete('Litter box clean') -> spawned: '{next_litter.title}' due {next_litter.due_date}")
print(f"  mark_task_complete('Brushing')         -> spawned: '{next_brush.title}' due {next_brush.due_date}")

print("\nLuna's recurring tasks AFTER completing:")
print_recurring_demo(alex_sched, "original tasks (done) + auto-spawned tasks (pending)")

# Also show Mochi (was completed earlier in the filter section)
print("\nMochi's recurring tasks (completed earlier in filter demo):")
print_recurring_demo(jordan_sched, "Morning walk + Feeding spawned new instances")

# ---------------------------------------------------------------------------
# Section 4 — generate(): full schedule (uses priority + time sort internally)
# ---------------------------------------------------------------------------

print("\n" + "#" * 50)
print("# FULL GENERATED SCHEDULES")
print("#" * 50 + "\n")

print_schedule(jordan, jordan_sched.generate())
print_schedule(alex,   alex_sched.generate())


# ---------------------------------------------------------------------------
# Section 4 — Conflict detection
# ---------------------------------------------------------------------------

print("\n" + "#" * 50)
print("# CONFLICT DETECTION")
print("#" * 50)

# --- 4a: same-pet overlap (manually constructed) ----------------------------
# The sequential generate() never stacks tasks, so we build a Schedule by
# hand with two deliberately overlapping ScheduledTask objects.
#
#   Feeding      07:00 - 07:10   (10 min)
#   Morning walk 07:05 - 07:35   (30 min)   <-- starts 5 min into Feeding

print("\n  -- Same-pet overlap (manually constructed schedule) --")

conflict_pet = Pet(name="Mochi", species=Species.DOG)
conflict_owner = Owner(name="Jordan", pet=conflict_pet,
                       day_start=time(7, 0), day_end=time(9, 0))
conflict_sched = Scheduler(owner=conflict_owner)

task_feeding = Task("Feeding",      10, Priority.HIGH, preferred_time=time(7, 0))
task_walk    = Task("Morning walk", 30, Priority.HIGH, preferred_time=time(7, 5))

overlapping_schedule = Schedule(
    scheduled=[
        ScheduledTask(task_feeding, time(7, 0),  time(7, 10)),  # 07:00 - 07:10
        ScheduledTask(task_walk,    time(7, 5),  time(7, 35)),  # 07:05 - 07:35  OVERLAP
    ],
    skipped=[],
    total_minutes_available=conflict_owner.available_minutes(),
)

same_pet_warnings = conflict_sched.check_conflicts(overlapping_schedule)

if same_pet_warnings:
    for msg in same_pet_warnings:
        print(f"  {msg}")
else:
    print("  No same-pet conflicts found.")

# --- 4b: normal schedules have no same-pet conflicts ------------------------
print("\n  -- Normal generated schedules (no same-pet conflicts expected) --")

jordan_gen = jordan_sched.generate()
alex_gen   = alex_sched.generate()

for owner, sched, sched_obj in [
    (jordan, jordan_sched, jordan_gen),
    (alex,   alex_sched,   alex_gen),
]:
    w = sched.check_conflicts(sched_obj)
    label = f"{owner.name}/{owner.pet.name}"
    if w:
        for msg in w:
            print(f"  {msg}")
    else:
        print(f"  {label}: no same-pet conflicts.")

# --- 4c: cross-pet overlap ---------------------------------------------------
# Jordan cares for Mochi 07:00-09:00 and Alex cares for Luna 08:00-09:30.
# Their windows overlap from 08:00-09:00, so a single pet-sitter handling
# both would face back-to-back or overlapping tasks in that window.

print("\n  -- Cross-pet overlap (Jordan + Alex share 08:00-09:00 window) --")

pairs = [(jordan, jordan_gen), (alex, alex_gen)]
cross_warnings = Scheduler.cross_pet_conflicts(pairs)

if cross_warnings:
    for msg in cross_warnings:
        print(f"  {msg}")
else:
    print("  No cross-pet conflicts found.")

# --- 4d: confirm cross-pet fires for a sitter with identical windows --------
# One sitter manages BOTH pets in the exact same 08:00-09:00 block —
# every task will overlap its counterpart from the other pet.

print("\n  -- Same-window sitter scenario (all tasks overlap) --")

sitter_jordan = Owner(name="Sitter", pet=mochi, day_start=time(8, 0), day_end=time(9, 0))
sitter_alex   = Owner(name="Sitter", pet=luna,  day_start=time(8, 0), day_end=time(9, 0))

sitter_mochi_sched = Scheduler(owner=sitter_jordan).generate()
sitter_luna_sched  = Scheduler(owner=sitter_alex).generate()

sitter_pairs = [(sitter_jordan, sitter_mochi_sched), (sitter_alex, sitter_luna_sched)]
sitter_warnings = Scheduler.cross_pet_conflicts(sitter_pairs)

if sitter_warnings:
    for msg in sitter_warnings:
        print(f"  {msg}")
else:
    print("  No cross-pet conflicts found.")
print()
