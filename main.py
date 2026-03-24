from datetime import time
from pawpal_system import Owner, Pet, Task, Scheduler, Priority, Species


mochi = Pet(
    name="Mochi",
    species=Species.DOG,
    tasks=[
        Task(title="Morning walk",     duration_minutes=30, priority=Priority.HIGH),
        Task(title="Feeding",          duration_minutes=10, priority=Priority.HIGH),
        Task(title="Grooming session", duration_minutes=45, priority=Priority.MEDIUM),
        Task(title="Enrichment play",  duration_minutes=20, priority=Priority.LOW),
    ],
)

luna = Pet(
    name="Luna",
    species=Species.CAT,
    tasks=[
        Task(title="Litter box clean", duration_minutes=10, priority=Priority.HIGH),
        Task(title="Feeding",          duration_minutes=10, priority=Priority.HIGH),
        Task(title="Laser play",       duration_minutes=15, priority=Priority.MEDIUM),
        Task(title="Brushing",         duration_minutes=20, priority=Priority.LOW),
        Task(title="Vet call",         duration_minutes=60, priority=Priority.LOW),
    ],
)

jordan = Owner(name="Jordan", pet=mochi, day_start=time(7, 0),  day_end=time(9, 0))
alex   = Owner(name="Alex",   pet=luna,  day_start=time(8, 0),  day_end=time(9, 30))


def print_schedule(owner: Owner, schedule) -> None:
    print("=" * 50)
    print(f"Today's Schedule — {owner.name} & {owner.pet.name} ({owner.pet.species.value})")
    print(f"Window: {owner.day_start.strftime('%H:%M')} – {owner.day_end.strftime('%H:%M')}")
    print("=" * 50)

    if not schedule.scheduled:
        print("  No tasks could be scheduled in this window.")
    else:
        for st in schedule.scheduled:
            print(
                f"  {st.start_time.strftime('%H:%M')} – {st.end_time.strftime('%H:%M')}"
                f"  [{st.task.priority.name:<6}]  {st.task.title}"
            )

    if schedule.skipped:
        print()
        print("  [!] Skipped (not enough time):")
        for t in schedule.skipped:
            print(f"    - {t.title} ({t.duration_minutes} min, {t.priority.name})")

    print()
    print(" ", schedule.summary())
    print()


jordan_schedule = Scheduler(owner=jordan).generate()
alex_schedule   = Scheduler(owner=alex).generate()

print_schedule(jordan, jordan_schedule)
print_schedule(alex, alex_schedule)
