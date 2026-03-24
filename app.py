import json
import streamlit as st
import pandas as pd
from datetime import time
from pathlib import Path
from pawpal_system import Owner, Pet, Task, Scheduler, Priority, Species

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ── Disk persistence ───────────────────────────────────────────────────────────
DATA_FILE = Path(__file__).parent / "pawpal_data.json"

def save_to_disk(owner, tasks):
    if owner is None:
        return
    data = {
        "owner": {
            "name":      owner.name,
            "pet_name":  owner.pet.name,
            "species":   owner.pet.species.value,
            "day_start": owner.day_start.strftime("%H:%M"),
            "day_end":   owner.day_end.strftime("%H:%M"),
        },
        "tasks": [
            {
                "title":            t.title,
                "duration_minutes": t.duration_minutes,
                "priority":         t.priority.name,
                "completed":        t.completed,
            }
            for t in tasks
        ],
    }
    DATA_FILE.write_text(json.dumps(data, indent=2))


def load_from_disk():
    if not DATA_FILE.exists():
        return None, []
    data = json.loads(DATA_FILE.read_text())
    o = data["owner"]
    h_start, m_start = map(int, o["day_start"].split(":"))
    h_end,   m_end   = map(int, o["day_end"].split(":"))
    tasks = [
        Task(
            title=t["title"],
            duration_minutes=t["duration_minutes"],
            priority=Priority[t["priority"]],
        )
        for t in data["tasks"]
    ]
    for task, t in zip(tasks, data["tasks"]):
        task.completed = t["completed"]
    pet   = Pet(name=o["pet_name"], species=Species(o["species"]), tasks=tasks)
    owner = Owner(
        name=o["name"], pet=pet,
        day_start=time(h_start, m_start),
        day_end=time(h_end, m_end),
    )
    return owner, tasks


# ── Session state vault ────────────────────────────────────────────────────────
# On the very first run of a fresh session, reload from disk so a browser
# refresh does not wipe the user's data.
if "loaded" not in st.session_state:
    owner, tasks = load_from_disk()
    st.session_state.owner     = owner
    st.session_state.pet       = owner.pet if owner else None
    st.session_state.tasks     = tasks
    st.session_state.schedule  = None
    st.session_state.scheduler = None
    st.session_state.loaded    = True

# ── Owner & Pet form ───────────────────────────────────────────────────────────
st.subheader("Owner & Pet")

saved_owner = st.session_state.owner
col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value=saved_owner.name      if saved_owner else "Jordan")
    pet_name   = st.text_input("Pet name",   value=saved_owner.pet.name  if saved_owner else "Mochi")
    species    = st.selectbox("Species", ["dog", "cat", "other"],
                              index=["dog","cat","other"].index(saved_owner.pet.species.value) if saved_owner else 0)
with col2:
    day_start = st.time_input("Available from",  value=saved_owner.day_start if saved_owner else time(7, 0))
    day_end   = st.time_input("Available until", value=saved_owner.day_end   if saved_owner else time(9, 0))

if st.button("Save owner & pet"):
    if day_end <= day_start:
        st.error("End time must be after start time.")
    else:
        pet   = Pet(name=pet_name, species=Species(species), tasks=st.session_state.tasks)
        owner = Owner(name=owner_name, pet=pet, day_start=day_start, day_end=day_end)
        st.session_state.pet       = pet
        st.session_state.owner     = owner
        st.session_state.schedule  = None
        st.session_state.scheduler = None
        save_to_disk(owner, st.session_state.tasks)
        st.success(f"Saved! {owner_name} & {pet_name} — {day_start.strftime('%H:%M')} to {day_end.strftime('%H:%M')}")

st.divider()

# ── Task management ────────────────────────────────────────────────────────────
st.subheader("Tasks")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["high", "medium", "low"])

if st.button("Add task"):
    new_task = Task(
        title=task_title,
        duration_minutes=int(duration),
        priority=Priority[priority.upper()],
    )
    st.session_state.tasks.append(new_task)
    if st.session_state.pet is not None:
        st.session_state.pet.tasks = st.session_state.tasks
    st.session_state.schedule  = None
    st.session_state.scheduler = None
    save_to_disk(st.session_state.owner, st.session_state.tasks)

# ── Smart task table with filter ───────────────────────────────────────────────
if st.session_state.tasks:
    filter_choice = st.radio("Show", ["All", "Pending", "Completed"], horizontal=True)
    completed_filter = None
    if filter_choice == "Pending":
        completed_filter = False
    elif filter_choice == "Completed":
        completed_filter = True

    # Use Scheduler.filter_tasks() to drive the display
    if st.session_state.owner:
        preview_sched = Scheduler(owner=st.session_state.owner)
        displayed = preview_sched.filter_tasks(completed=completed_filter)
    else:
        displayed = [t for t in st.session_state.tasks
                     if completed_filter is None or t.completed == completed_filter]

    PRIORITY_COLOR = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
    if displayed:
        table_rows = [
            {
                "Task":           PRIORITY_COLOR[t.priority.name] + " " + t.title,
                "Duration (min)": t.duration_minutes,
                "Priority":       t.priority.name,
                "Status":         "✓ Done" if t.completed else "Pending",
            }
            for t in displayed
        ]
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
    else:
        st.info(f"No {filter_choice.lower()} tasks.")

    # Remove buttons (only in All / Pending view)
    if filter_choice != "Completed":
        pending = [t for t in st.session_state.tasks if not t.completed]
        for i, t in enumerate(pending):
            col_info, col_btn = st.columns([5, 1])
            with col_info:
                st.caption(f"{t.title} — {t.duration_minutes} min · {t.priority.name}")
            with col_btn:
                if st.button("Remove", key=f"remove_{i}"):
                    st.session_state.tasks.remove(t)
                    if st.session_state.pet is not None:
                        st.session_state.pet.tasks = st.session_state.tasks
                    st.session_state.schedule  = None
                    st.session_state.scheduler = None
                    save_to_disk(st.session_state.owner, st.session_state.tasks)
                    st.rerun()
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ── Schedule generation ────────────────────────────────────────────────────────
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if st.session_state.owner is None:
        st.warning("Please save an owner & pet first.")
    elif not st.session_state.tasks:
        st.warning("Please add at least one task.")
    else:
        st.session_state.owner.pet.tasks = st.session_state.tasks
        scheduler = Scheduler(owner=st.session_state.owner)
        st.session_state.schedule  = scheduler.generate()
        st.session_state.scheduler = scheduler

# ── Schedule display ───────────────────────────────────────────────────────────
if st.session_state.schedule is not None:
    schedule  = st.session_state.schedule
    scheduler = st.session_state.scheduler
    owner     = st.session_state.owner

    st.markdown(
        f"**{owner.name} & {owner.pet.name}** — "
        f"{owner.day_start.strftime('%H:%M')} to {owner.day_end.strftime('%H:%M')}"
    )

    # Time utilization metrics
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Window", f"{schedule.total_minutes_available} min")
    col_b.metric("Scheduled", f"{schedule.total_minutes_scheduled} min")
    col_c.metric("Tasks placed", len(schedule.scheduled))

    # Conflict check using Scheduler.check_conflicts()
    if scheduler is not None:
        conflicts = scheduler.check_conflicts(schedule)
        if conflicts:
            for warning_msg in conflicts:
                st.warning(warning_msg)
        elif schedule.scheduled:
            st.success("No scheduling conflicts detected.")

    if not schedule.scheduled:
        st.error("No tasks fit in the available window.")
    else:
        PRIORITY_ICON = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
        for i, s in enumerate(schedule.scheduled):
            icon       = PRIORITY_ICON[s.task.priority.name]
            time_label = f"{s.start_time.strftime('%H:%M')} → {s.end_time.strftime('%H:%M')}"
            col_time, col_task, col_done = st.columns([2, 5, 1])
            with col_time:
                st.write(time_label)
            with col_task:
                if s.task.completed:
                    st.success(f"~~{s.task.title}~~ · Done")
                else:
                    st.markdown(
                        f"{icon} **{s.task.title}** — {s.task.duration_minutes} min · `{s.task.priority.name}`"
                    )
            with col_done:
                if not s.task.completed:
                    if st.button("Done", key=f"done_{i}"):
                        # Use scheduler.mark_task_complete() so recurring tasks
                        # automatically spawn their next occurrence
                        next_task = scheduler.mark_task_complete(s.task)
                        if next_task is not None:
                            st.session_state.tasks.append(next_task)
                            if st.session_state.pet is not None:
                                st.session_state.pet.tasks = st.session_state.tasks
                        save_to_disk(st.session_state.owner, st.session_state.tasks)
                        st.rerun()
                else:
                    st.write("✓")

    if schedule.skipped:
        st.warning(f"⚠️ {len(schedule.skipped)} task(s) could not be scheduled — not enough time.")
        skipped_rows = [
            {
                "Task":           PRIORITY_ICON[t.priority.name] + " " + t.title,
                "Duration (min)": t.duration_minutes,
                "Priority":       t.priority.name,
            }
            for t in schedule.skipped
        ]
        st.table(pd.DataFrame(skipped_rows))

    st.info(schedule.summary())
