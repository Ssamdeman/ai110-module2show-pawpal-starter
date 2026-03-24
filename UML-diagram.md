# PawPal+ — UML Class Diagram

Paste the code block below into [https://mermaid.live](https://mermaid.live)

```
classDiagram
    class Owner {
        +str name
        +time day_start
        +time day_end
        +available_minutes() int
    }

    class Pet {
        +str name
        +Species species
    }

    class Task {
        +str title
        +int duration_minutes
        +Priority priority
    }

    class Priority {
        <<enumeration>>
        HIGH
        MEDIUM
        LOW
    }

    class Species {
        <<enumeration>>
        DOG
        CAT
        OTHER
    }

    class ScheduledTask {
        +Task task
        +time start_time
        +time end_time
    }

    class Schedule {
        +list~ScheduledTask~ scheduled
        +list~Task~ skipped
        +int total_minutes_available
        +int total_minutes_scheduled
        +summary() str
    }

    class Scheduler {
        +Owner owner
        +list~Task~ tasks
        +generate() Schedule
    }

    Owner "1" --> "1" Pet : owns
    Scheduler --> Owner : uses
    Scheduler --> "0..*" Task : receives
    Scheduler --> Schedule : produces
    Schedule *-- "0..*" ScheduledTask : contains
    Schedule o-- "0..*" Task : skipped
    ScheduledTask --> Task : wraps
    Task --> Priority : has
    Pet --> Species : has
```
