# PawPal+ — UML Class Diagram

Paste the code block below into [https://mermaid.live](https://mermaid.live)

```
classDiagram
    %% ── Enumerations ─────────────────────────────────────────────────────────

    class Priority {
        <<enumeration>>
        HIGH = 1
        MEDIUM = 2
        LOW = 3
    }

    class Species {
        <<enumeration>>
        DOG = "dog"
        CAT = "cat"
        OTHER = "other"
    }

    class RecurrenceType {
        <<enumeration>>
        NONE = "none"
        DAILY = "daily"
        WEEKLY = "weekly"
    }

    %% ── Core domain classes ──────────────────────────────────────────────────

    class Owner {
        +str name
        +Pet pet
        +time day_start
        +time day_end
        +available_minutes() int
    }

    class Pet {
        +str name
        +Species species
        +list~Task~ tasks
    }

    class Task {
        +str title
        +int duration_minutes
        +Priority priority
        +time preferred_time
        +RecurrenceType recurrence
        +date due_date
        +bool completed
        +mark_complete() None
        +spawn_next() Task|None
    }

    %% ── Scheduling classes ───────────────────────────────────────────────────

    class ScheduledTask {
        +Task task
        +time start_time
        +time end_time
    }

    class Schedule {
        +list~ScheduledTask~ scheduled
        +list~Task~ skipped
        +int total_minutes_available
        +int /total_minutes_scheduled
        +summary() str
    }

    class Scheduler {
        +Owner owner
        +generate() Schedule
        +sort_by_time() list~Task~
        +filter_tasks(completed, pet_name) list~Task~
        +mark_task_complete(task) Task|None
        +check_conflicts(schedule) list~str~
        +cross_pet_conflicts(pairs)$ list~str~
    }

    %% ── Module-level utility functions (pawpal_system.py top level) ──────────

    class SchedulingUtils {
        <<utility>>
        +filter_tasks(tasks, pet_name, completed)$ list~Task~
        +filter_tasks_by_pet(owners, pet_name)$ list~Task~
        +detect_conflicts(schedules)$ list~str~
    }

    %% ── Relationships ────────────────────────────────────────────────────────

    Owner "1" --> "1" Pet : owns
    Pet "1" --> "0..*" Task : has

    Task --> Priority : has
    Task --> RecurrenceType : has
    Task --> Task : spawn_next() creates

    Scheduler --> Owner : uses
    Scheduler --> Schedule : produces

    Schedule *-- "0..*" ScheduledTask : contains
    Schedule o-- "0..*" Task : skipped
    ScheduledTask --> Task : wraps

    Pet --> Species : has

    SchedulingUtils ..> Owner : references
    SchedulingUtils ..> Schedule : references
    SchedulingUtils ..> Task : operates on
```