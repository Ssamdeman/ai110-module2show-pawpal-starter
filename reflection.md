# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

I made a set of classes that covered all the requirements:

- Owner — holds name + time window, computes available minutes
- Pet — name + species (enum)
- Task — title, duration, priority (enum)
- Scheduler — takes owner + tasks, runs generate() and returns a Schedule
- ScheduledTask — wraps a Task with start/end times
- Schedule — holds scheduled tasks, skipped tasks, and a summary
- Priority — enum: HIGH / MEDIUM / LOW
- Species — enum: DOG / CAT / OTHER

**b. Design changes**

Yeah, the design changed. Three bugs I caught before writing real code:

1. Owner had no Pet field — the UML drew an arrow but there was no actual attribute, so the Scheduler had no way to reach the pet.
2. `datetime.time` can't do math — `time(9,0) - time(7,0)` just crashes. Had to switch to `datetime.combine` + `timedelta`.
3. `total_minutes_scheduled` was going to be a constructor param — that's just asking for the caller to pass the wrong number. Made it computed instead.

Priority also ended up mattering way more than I originally planned. It basically became the main sorting key for everything.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

Three constraints: available time window (hard limit — tasks that don't fit get skipped), task priority (HIGH always goes before MEDIUM/LOW), and preferred_time (tiebreaker within the same priority).

Priority mattered most because pet care has real urgency — a medication isn't the same as enrichment play. Time is a hard physical wall. Preferred_time is more of a "nice to have."

**b. Tradeoffs**

The scheduler is greedy — sort once by (priority, preferred_time), walk the list, place it if it fits, skip it if it doesn't. Simple.

The downside: if a 45-min grooming session blocks the next slot and there's only 20 min left, a smarter algorithm might backtrack and squeeze in something smaller. This one won't.

Honestly that's fine here. Pet care lists are like 5-10 tasks. The performance gain from a full bin-packing solver isn't worth the complexity. And the skipped list tells the owner exactly what got dropped so they can adjust their window themselves.

One thing I specifically kept separate: conflict checking stays outside of `generate()`. Mixing them in one function would've made both harder to test.

---

## 3. AI Collaboration

**a. How you used AI**

Mainly for design work and catching issues before I wrote anything. I'd paste my UML plan and ask "does this make sense, what's broken" — that's where the three bugs above came from. Way more useful than debugging code that's already wrong.

The prompts that actually helped: giving AI a specific role ("act as a senior Python dev reviewing this design") and asking for short responses. When I just asked open questions I got walls of text that weren't useful.

**b. Judgment and verification**

There was a schedule generation approach AI suggested that I didn't understand at first. Instead of just copy-pasting it, I asked it to walk me through the logic step by step. Once I understood it I rewrote it myself in a way that made sense to me. The final code isn't what AI wrote — it's what I understood well enough to write.

---

## 4. AI Strategy — VS Code Copilot

**Which Copilot features helped most**

Autocomplete was the most useful day-to-day thing. Especially for repetitive stuff like the `__init__` methods and the enum definitions — Copilot would fill those out after the first one and I mostly just had to confirm. For `check_conflicts` it suggested the `itertools.combinations` approach which I wouldn't have thought of that fast.

Inline chat was good for quick "what does this line actually do" questions without breaking focus to open a browser.

**One suggestion I rejected**

Copilot wanted to put conflict checking inside `generate()` — like one combined function that schedules and checks at the same time. I said no. If those are mixed together you can't test them independently and `generate()` becomes this big thing that's doing too much. Keeping them separate was the right call and I'm glad I pushed back on that.

**Separate chat sessions per phase**

This actually helped a lot. Phase 1 was just design/UML, Phase 2 was implementation, Phase 3 was the smarter methods. Each session stayed focused on one thing so I wasn't carrying around a bunch of context from earlier phases that didn't matter anymore. When I tried mixing phases in one session the responses got confused about what was already built vs what was being planned.

**Being the "lead architect"**

AI is good at filling in details and catching small mistakes. It's not good at knowing what you actually want to build or why. Every time I let it drive — like just asking "write me a scheduler" — I got something generic that didn't fit the design. The times it worked were when I already had a clear plan and used AI to check it or fill in the repetitive parts. You have to know enough to tell when the suggestion is wrong. That's the job.

---

## 5. Testing and Verification

**a. What you tested**

Three areas: sorting (right order, None times go last, priority wins over time), recurrence (daily task creates a new one for the next day, pet.tasks grows by 1), conflict detection (overlapping slots get flagged, back-to-back don't).

Those three because they're the easiest to get subtly wrong without noticing.

**b. Confidence**

4/5. All 11 tests pass. Knocked one off because the greedy scheduler can miss valid schedules in weird edge cases, and I haven't tested cross-pet conflicts with real generated schedules — only manually built ones.

---

## 6. Reflection

**a. What went well**

The Scheduler class. Adding the Phase 3 methods (`sort_by_time`, `filter_tasks`, `mark_task_complete`, `check_conflicts`) didn't require touching anything that was already working. That's the payoff of separating concerns early — you can add stuff without breaking what's there.

**b. What I'd improve**

Two things. First, let the owner manually reorder tasks after the schedule is generated — right now the algorithm decides everything and there's no override. Second, save `preferred_time` and `recurrence` to the JSON file. Those fields exist in the class but don't survive a browser refresh, which makes recurrence kind of pointless in the current UI.

**c. Key takeaway**

Use AI at the design stage, not the debugging stage. Catching the three structural bugs before writing code saved a lot of time. Trying to use AI to debug broken logic after the fact was way less useful — it doesn't have the context for why you made the choices you made. Plan first, verify with AI, then build.
