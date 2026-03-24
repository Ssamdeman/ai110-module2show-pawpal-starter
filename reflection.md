# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?
Answer: 
made many classes that met all requirements 

Owner:	Holds name + time window, computes available minutes
Pet	Name + species (enum)
Task:	Title, duration, priority (enum)
Scheduler:	Takes owner + tasks, runs generate() → returns a Schedule
ScheduledTask:	Wraps a Task with assigned start/end times 
Schedule: Holds scheduled tasks, skipped tasks, and a su
Priority:	Enum: HIGH / MEDIUM / LOW
Species	Enum: DOG / CAT / OTHER


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Initially I was thinking about priority, but now it became the most important thing, so now I am really using it as well as the tasks itself — it will depend on the priority. 
and the fixed 3 issues:
 Owner has no Pet — the UML shows Owner → Pet but they're completely disconnected. The Scheduler can never know which pet it's planning for.

datetime.time can't do arithmetic — time(9,0) - time(7,0) throws a TypeError in Python. available_minutes() will crash the moment you implement it. Need datetime/timedelta available.

total_minutes_scheduled is a constructor param — it's always derivable from the scheduled list, so passing it in is a future bug waiting to happen (caller could pass the wrong number). Should be computed. 

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler considers three constraints: the owner's available time window (hard limit — tasks that don't fit are skipped entirely), task priority (HIGH tasks are always attempted before MEDIUM or LOW), and preferred_time (a soft tiebreaker within the same priority band — earlier preferred times are scheduled first).

Priority was the most important because pet care has real urgency differences: a vet appointment or medication is not the same as an optional enrichment game. Time window is a hard physical constraint — you cannot schedule 3 hours of tasks into a 1-hour window. Preferred_time is secondary because it is "nice to have" rather than a requirement.


**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

**Tradeoff: greedy first-fit scheduling — speed over optimal packing**

`Scheduler.generate()` uses a greedy first-fit algorithm: it sorts tasks once by
(priority, preferred_time) and then walks the list in order, placing each task if
it fits in the remaining time, skipping it permanently if it does not.

Example of the problem this creates:
  Remaining time: 20 minutes
  Next task in sorted order: Grooming session — 45 min  → SKIPPED
  Task after that: Enrichment play — 20 min              → placed

The greedy approach gets Enrichment play scheduled, which is correct here.


A smarter scheduler would backtrack and try Task C before Task B, fitting a
second HIGH-priority task instead of a MEDIUM one. The greedy approach misses this.

**Why this tradeoff is reasonable for PawPal+:**

1. Pet care schedules are small — typically 5–10 tasks per day. The performance
   difference between greedy O(n log n) and an optimal bin-packing solver
   (NP-hard in general) is irrelevant at this scale.

2. Priority + preferred_time sorting means the greedy algorithm almost always
   makes the right call: HIGH tasks are tried first, so they get placed unless
   the window is genuinely too short for them.

3. The "skipped" list gives the owner immediate visibility into what was dropped,
   so they can manually adjust the time window rather than relying on the
   scheduler to figure out an exotic rearrangement.

**What was NOT chosen (and why):**
Overlapping-duration conflict detection inside generate() was skipped in favor of
the separate check_conflicts() method. Mixing scheduling and conflict-checking in
one function would make generate() harder to test and reason about independently.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
    desinginsds and fixing come code verify my plannig before even doing any code.
- What kinds of prompts or questions were most helpful?
    give me role and resudce thier explaniotna an make short resaponces 

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
    there is scheulde it was given it did nto make sense I asked to epxlain it btter and using atomic thinking and it id and able to get m
- How did you evaluate or verify what the AI suggested?
    Re do it again with specifsi the issue I was struggle it 

---

## 4. Testing and Verification

**a. What you tested**

I tested three main things: sorting (tasks come back in the right order, None times go last, priority beats preferred time), recurrence (completing a daily task actually creates a new one for the next day), and conflict detection (overlapping slots get flagged, back-to-back ones don't).

These mattered because sorting and conflicts are easy to get subtly wrong — like thinking adjacent slots are overlapping, or assuming time always beats priority.

**b. Confidence**

4/5. All 11 tests pass and the logic holds up on the cases I threw at it. I knocked off one star because the greedy scheduler can miss valid schedules in tricky situations (a big task blocking smaller ones behind it), and I haven't tested cross-pet conflicts with real generated schedules yet.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

The part I am most satisfied with is the `Scheduler` class and how cleanly the Phase 3 methods (`sort_by_time`, `filter_tasks`, `mark_task_complete`, `check_conflicts`) fit into the design without needing to rewrite anything. The separation between `generate()` (builds the schedule) and `check_conflicts()` (validates it) paid off — I could add conflict detection without touching the scheduling algorithm at all. The UI update in Phase 4 also went smoothly because the backend logic was already solid: all I had to do was call the right methods and pass results to Streamlit components.

**b. What you would improve**

If I had another iteration, I would improve two things. First, I would add a drag-and-drop or manual override so the owner can reorder tasks after the schedule is generated — right now the scheduler decides everything and the user has no way to say "move the walk to later." Second, I would persist `preferred_time` and `recurrence` through the JSON file so recurring tasks and time preferences survive a browser refresh. Currently those fields exist in the class but are not saved to disk, which means they reset every session.

**c. Key takeaway**

The most important thing I learned is that AI is best used at the design stage, not the debugging stage. When I used AI to verify my class diagram and catch structural bugs (like `available_minutes()` crashing because `time` objects can't do arithmetic) *before writing any code*, it saved a lot of time. When I tried to use it to debug an already-broken piece of logic, the answers were less useful because I hadn't given the AI enough context about what the code was supposed to do. Starting with a clear plan and verifying it with AI first made the actual implementation much smoother.
