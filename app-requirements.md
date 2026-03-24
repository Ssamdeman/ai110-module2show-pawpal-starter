# PawPal+ — App Requirements

---

## 1. Data: Owner

- Owner has a **name** (text)
- Owner has a **day start time** (e.g., 07:00)
- Owner has a **day end time** (e.g., 09:00)
- The window between start and end defines total available minutes for the day
- End time must be after start time

---

## 2. Data: Pet

- Pet has a **name** (text)
- Pet has a **species**: dog, cat, or other

---

## 3. Data: Task

- Task has a **title** (text)
- Task has a **duration** in minutes (integer, minimum 1)
- Task has a **priority**: high, medium, or low

---

## 4. Task Management (UI)

- User can **add** a task by entering title, duration, and priority
- User can **remove** a task from the list
- The current task list is always visible before generating a schedule
- Task list persists within the session (not cleared on page interaction)

---

## 5. Scheduling Logic

- Scheduler receives: the owner's time window, and the list of tasks
- Scheduler calculates total available minutes from the time window
- Tasks are sorted by priority: high → medium → low
- Tasks are scheduled greedily in priority order, assigned sequential start/end times starting from the window start time
- A task is **included** if it fits within the remaining available time
- A task is **skipped** if it does not fit (not enough remaining time)
- Once a task is skipped due to time, all remaining lower-or-equal priority tasks are also evaluated (a shorter task of equal priority can still fit if there is room)

---

## 6. Schedule Output (UI)

- Display the owner name, pet name, and the time window
- Display each **scheduled task** as a row showing: task title, start time, end time, duration, priority
- Times are shown in HH:MM format
- Display a clear **warning** if any tasks were skipped
- For each **skipped task**, show: task title, duration, priority, and reason ("not enough time remaining")

---

## 7. Explanation / Reasoning

- After the schedule table, show a brief explanation for each scheduled task: why it was placed (its priority level and available time at that point)
- Show a summary line: total minutes scheduled vs total minutes available

---

## 8. Edge Cases the App Must Handle

- No tasks added → show a message instead of generating a schedule
- All tasks fit in the window → no warning shown
- No tasks fit in the window → warn that no tasks could be scheduled
- Single task → scheduled normally if it fits, skipped with warning if it doesn't
- Two tasks with the same priority competing for remaining time → shorter one can be tried first if the longer one doesn't fit

---

## 9. Tests (pytest)

- All tasks fit → all appear in schedule, none skipped
- Total task time exceeds window → lowest priority tasks are skipped, warning is produced
- Empty task list → scheduler returns empty schedule without crashing
- Single task fits → appears in schedule with correct start/end times
- Single task does not fit → skipped with warning
- Tasks are ordered high → medium → low in output regardless of input order
- Two tasks of equal priority, only one fits → shorter one is scheduled if it fits
