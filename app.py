
import json
import re
import datetime as dt
import requests
import streamlit as st
from pathlib import Path
import sqlite3

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="Lumi | AI Planner",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- LOAD UI STYLES ----------------

css_file = Path(__file__).parent / "style.css"

st.markdown(
    f"<style>{css_file.read_text(encoding='utf-8')}</style>",
    unsafe_allow_html=True
)


# ---------------- PERMANENT STORAGE ----------------

DB_PATH = Path(__file__).parent / "planora.db"


def json_encode(value):
    """Convert Python dates and times into JSON-compatible values."""
    if isinstance(value, dt.datetime):
        return {"__planora_type__": "datetime", "value": value.isoformat()}
    if isinstance(value, dt.date):
        return {"__planora_type__": "date", "value": value.isoformat()}
    if isinstance(value, dt.time):
        return {"__planora_type__": "time", "value": value.isoformat()}
    raise TypeError(f"Cannot save {type(value).__name__}")


def json_decode(value):
    """Restore dates and times when loading saved data."""
    kind = value.get("__planora_type__")

    if kind == "datetime":
        return dt.datetime.fromisoformat(value["value"])
    if kind == "date":
        return dt.date.fromisoformat(value["value"])
    if kind == "time":
        return dt.time.fromisoformat(value["value"])

    return value


def init_database():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS app_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                data TEXT NOT NULL
            )
        """)


def save_data():
    data = {
        "tasks": st.session_state.get("tasks", []),
        "projects": st.session_state.get("projects", ["General"]),
        "ai_tasks": st.session_state.get("ai_tasks", [])
    }

    saved_json = json.dumps(data, default=json_encode)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO app_state (id, data)
            VALUES (1, ?)
            ON CONFLICT(id) DO UPDATE SET data = excluded.data
        """, (saved_json,))


def load_data():
    init_database()

    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT data FROM app_state WHERE id = 1"
        ).fetchone()

    if row:
        return json.loads(row[0], object_hook=json_decode)

    return {
        "tasks": [],
        "projects": ["General"],
        "ai_tasks": []
    }


# Load saved information when a Streamlit session starts.
if "storage_initialized" not in st.session_state:
    if "tasks" not in st.session_state:
        saved_data = load_data()
        st.session_state.tasks = saved_data["tasks"]
        st.session_state.projects = saved_data["projects"]
        st.session_state.ai_tasks = saved_data["ai_tasks"]
    else:
        # Preserve tasks already present in the current session.
        st.session_state.setdefault("ai_tasks", [])
        st.session_state.setdefault("projects", ["General"])
        init_database()
        save_data()

    st.session_state.storage_initialized = True
else:
    # Persist changes before each Streamlit rerun redraws the page.
    save_data()


# Add new fields to tasks created by the older version.
for item in st.session_state.tasks:
    item.setdefault("deadline", "Not specified")
    item.setdefault("due_date", None)
    item.setdefault("project", "General")
    item.setdefault("reminder_date", None)
    item.setdefault("reminder_time", dt.time(9, 0))
    item.setdefault("completed", False)

    if item["project"] not in st.session_state.projects:
        st.session_state.projects.append(item["project"])


def update_dashboard_task(index):
    key = f"dashboard_done_{index}"
    st.session_state.tasks[index]["completed"] = st.session_state[key]
    save_data()


# ---------------- AI INTEGRATION ----------------

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openrouter/free"


def organize_tasks(description):
    api_key = st.secrets["OPENROUTER_API_KEY"]
    today = dt.date.today().isoformat()

    prompt = f"""
You are an AI task planner. Today's date is {today}.

Extract the separate tasks from the user's description.
Assign High, Medium, or Low priority.
Never invent a deadline.
If a deadline can be converted to an unambiguous calendar date,
return that date as YYYY-MM-DD in due_date.
Otherwise set due_date to null.
Keep the user's stated deadline in deadline.
If none was specified, use "Not specified".

Return ONLY a valid JSON array. No Markdown.
Every task must contain:
task, priority, deadline, due_date.

Example:
[
  {{
    "task": "Finish assignment",
    "priority": "High",
    "deadline": "Tomorrow",
    "due_date": "YYYY-MM-DD"
  }}
]

Use a real date for due_date, not the example placeholder.
User description:
{description}
"""

    response = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        },
        timeout=60
    )

    if not response.ok:
        raise RuntimeError(
            f"OpenRouter HTTP {response.status_code}: "
            f"{response.text[:400]}"
        )

    content = response.json()["choices"][0]["message"]["content"]
    content = content.strip()
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    result = json.loads(content)
    if not isinstance(result, list):
        raise ValueError("The AI response was not a list.")

    cleaned = []

    for item in result:
        if not isinstance(item, dict):
            continue

        name = str(item.get("task", "")).strip()
        priority = str(item.get("priority", "Medium")).title()
        deadline = str(item.get("deadline", "Not specified")).strip()
        date_value = item.get("due_date")

        if not name:
            continue

        if priority not in ["High", "Medium", "Low"]:
            priority = "Medium"

        parsed_date = None
        if date_value:
            try:
                parsed_date = dt.date.fromisoformat(str(date_value))
            except ValueError:
                parsed_date = None

        cleaned.append({
            "task": name,
            "priority": priority,
            "deadline": deadline or "Not specified",
            "due_date": parsed_date,
            "project": "General",
            "reminder_date": parsed_date,
            "reminder_time": dt.time(9, 0),
            "completed": False
        })

    return cleaned


# ---------------- HEADER ----------------

st.markdown(
    '<div class="brand"><span>✦</span> LUMI '
    '<span style="background:transparent;color:#aaa8ca;'
    'font-size:.8rem;font-weight:500">AI PRODUCTIVITY SPACE</span></div>',
    unsafe_allow_html=True
)

st.markdown("""
<div class="hero">
    <small>YOUR DAY, YOUR WAY</small>
    <h1>Make room for what matters.</h1>
    <p>Plan your projects, organize your tasks, and keep your next
    deadline in sight — with a little help from AI.</p>
</div>
""", unsafe_allow_html=True)


# ---------------- DASHBOARD ----------------

tasks = st.session_state.tasks
total = len(tasks)
completed_count = sum(t["completed"] for t in tasks)
pending_count = total - completed_count
today = dt.date.today()

upcoming_count = sum(
    isinstance(t.get("due_date"), dt.date)
    and t["due_date"] >= today
    and not t["completed"]
    for t in tasks
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("✦ Total tasks", total)
c2.metric("◷ To do", pending_count)
c3.metric("✓ Completed", completed_count)
c4.metric("▦ Upcoming", upcoming_count)

if total:
    st.progress(
        completed_count / total,
        text=f"{round(completed_count / total * 100)}% completed"
    )

st.markdown(
    '<div class="muted">Navigate using the tabs below </div>',
    unsafe_allow_html=True
)


# ---------------- NAVIGATION ----------------

tab_home, tab_calendar, tab_projects, tab_board, tab_reminders = st.tabs([
    "⌂  Dashboard",
    "▦  Calendar",
    "▧  Projects",
    "☷  Task board",
    "◷  Reminders"
])


# ---------------- DASHBOARD TAB ----------------

with tab_home:
    st.markdown('<div class="section-title">✧ AI task planner</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="muted">Describe what is on your mind. '
        'AI will turn it into separate tasks.</div>',
        unsafe_allow_html=True
    )

    with st.container(border=True):
        with st.form("ai_planner_form"):
            description = st.text_area(
                "Describe your tasks",
                placeholder=(
                    "I have an assignment due tomorrow, "
                    "a test on Friday, and a room to clean..."
                ),
                height=110
            )
            ai_submit = st.form_submit_button(
                "✦ Organize with AI",
                type="primary",
                use_container_width=True
            )

        if ai_submit:
            if not description.strip():
                st.warning("Describe your tasks first.")
            else:
                try:
                    with st.spinner("AI is planning your tasks..."):
                        st.session_state.ai_tasks = organize_tasks(description)
                    st.rerun()
                except Exception as e:
                    st.error("The AI request failed.")
                    st.caption(str(e))

    if st.session_state.ai_tasks:
        st.markdown('<div class="section-title">Your AI plan</div>',
                    unsafe_allow_html=True)

        for n, item in enumerate(st.session_state.ai_tasks, start=1):
            with st.container(border=True):
                st.markdown(f"**{n}. {item['task']}**")
                st.markdown(
                    f'<span class="pill {item["priority"].lower()}">'
                    f'{item["priority"]} priority</span>',
                    unsafe_allow_html=True
                )
                st.markdown(
                    f'<div class="muted">Deadline: {item["deadline"]}</div>',
                    unsafe_allow_html=True
                )

        if st.button("＋ Add AI tasks to my list",
                     type="primary", use_container_width=True):
            existing = {
                t["task"].casefold() for t in st.session_state.tasks
            }
            added = 0

            for item in st.session_state.ai_tasks:
                if item["task"].casefold() not in existing:
                    st.session_state.tasks.append(item.copy())
                    existing.add(item["task"].casefold())
                    added += 1

            st.session_state.ai_tasks = []
            st.toast(f"Added {added} task(s)!")
            st.rerun()

    st.markdown('<div class="section-title">＋ Quick add</div>',
                unsafe_allow_html=True)

    project_options = st.session_state.projects or ["General"]

    with st.container(border=True):
        with st.form("manual_task_form", clear_on_submit=True):
            new_task = st.text_input(
                "Task name",
                placeholder="e.g. Finish my assignment"
            )

            col1, col2 = st.columns(2)
            with col1:
                new_priority = st.selectbox(
                    "Priority", ["High", "Medium", "Low"]
                )
                new_project = st.selectbox(
                    "Project", project_options
                )
            with col2:
                new_due = st.date_input(
                    "Deadline (optional)",
                    value=None
                )
                new_reminder_date = st.date_input(
                    "Reminder date (optional)",
                    value=None
                )

            new_reminder_time = st.time_input(
                "Reminder time",
                value=dt.time(9, 0)
            )

            manual_submit = st.form_submit_button(
                "＋ Add task",
                type="primary",
                use_container_width=True
            )

        if manual_submit:
            if not new_task.strip():
                st.warning("Enter a task name first.")
            else:
                deadline_text = (
                    new_due.strftime("%d %b %Y")
                    if new_due else "Not specified"
                )

                st.session_state.tasks.append({
                    "task": new_task.strip(),
                    "priority": new_priority,
                    "deadline": deadline_text,
                    "due_date": new_due,
                    "project": new_project,
                    "reminder_date": new_reminder_date,
                    "reminder_time": new_reminder_time,
                    "completed": False
                })
                st.toast("Task added!")
                st.rerun()

    st.markdown(
        '<div class="section-title">☷ Your task list</div>',
        unsafe_allow_html=True
    )

    priority_order = {"High": 0, "Medium": 1, "Low": 2}

    dashboard_tasks = sorted(
        enumerate(st.session_state.tasks),
        key=lambda pair: (
            pair[1].get("completed", False),
            priority_order.get(pair[1].get("priority", "Medium"), 1),
            pair[0]
        )
    )

    if not dashboard_tasks:
        st.info("Your tasks will appear here after you add them.")
    else:
        for i, item in dashboard_tasks:
            with st.container(border=True):
                col_task, col_check = st.columns([5, 1])

                with col_task:
                    st.markdown(
                        f"**{item['task']}**"
                    )
                    st.markdown(
                        f'<span class="pill '
                        f'{item.get("priority", "Medium").lower()}">'
                        f'{item.get("priority", "Medium")} priority'
                        f'</span>',
                        unsafe_allow_html=True
                    )
                    st.caption(
                        f"Deadline: {item.get('deadline', 'Not specified')}"
                    )

                with col_check:
                    st.checkbox(
    "Done",
    value=item.get("completed", False),
    key=f"dashboard_done_{i}",
    on_change=update_dashboard_task,
    args=(i,)
)
    st.markdown('<div class="section-title">Your day at a glance</div>',
                unsafe_allow_html=True)

    todays_tasks = [
        t for t in st.session_state.tasks
        if t.get("due_date") == today and not t["completed"]
    ]

    if todays_tasks:
        for item in todays_tasks:
            st.write(f"◷ **{item['task']}** · {item['priority']}")
    else:
        st.info("Nothing is due today, or no dated tasks have been added yet.")


# ---------------- CALENDAR TAB ----------------

with tab_calendar:
    st.markdown('<div class="section-title">▦ Calendar</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="muted">Choose a date to see the tasks scheduled for it.</div>',
        unsafe_allow_html=True
    )

    selected_date = st.date_input(
        "Select a date",
        value=today,
        key="calendar_selected_date"
    )

    dated_tasks = [
        t for t in st.session_state.tasks
        if t.get("due_date") == selected_date
    ]

    if dated_tasks:
        for item in dated_tasks:
            with st.container(border=True):
                st.markdown(f"**{item['task']}**")
                st.caption(
                    f"{item['priority']} priority · "
                    f"{item.get('project', 'General')} · "
                    f"{'Completed' if item['completed'] else 'To do'}"
                )
    else:
        st.info("No tasks with an editable calendar date on this day.")

    st.caption(
        "Tasks with only a text deadline, such as 'sometime next week', "
        "appear here once you assign them a calendar date in the task board."
    )


# ---------------- PROJECTS TAB ----------------

with tab_projects:
    st.markdown('<div class="section-title">▧ Projects</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="muted">Group tasks by assignment, subject, '
        'personal goals, or anything you are working on.</div>',
        unsafe_allow_html=True
    )

    with st.container(border=True):
        with st.form("project_form", clear_on_submit=True):
            project_name = st.text_input(
                "New project name",
                placeholder="e.g. College, Personal, AI Mini Project"
            )
            project_submit = st.form_submit_button(
                "＋ Create project",
                type="primary",
                use_container_width=True
            )

        if project_submit:
            clean_name = project_name.strip()
            if clean_name and clean_name not in st.session_state.projects:
                st.session_state.projects.append(clean_name)
                st.success(f"Created project: {clean_name}")
                st.rerun()
            elif clean_name:
                st.warning("That project already exists.")
            else:
                st.warning("Enter a project name.")

    st.markdown('<div class="section-title">Your projects</div>',
                unsafe_allow_html=True)

    for project in st.session_state.projects:
        project_tasks = [
            t for t in st.session_state.tasks
            if t.get("project", "General") == project
        ]
        project_done = sum(t["completed"] for t in project_tasks)

        with st.container(border=True):
            st.markdown(f"**▧ {project}**")
            st.caption(
                f"{len(project_tasks)} tasks · {project_done} completed"
            )
            if project_tasks:
                st.progress(project_done / len(project_tasks))

                for item in project_tasks:
                    st.write(
                        f"{'✓' if item['completed'] else '○'} "
                        f"{item['task']}"
                    )


# ---------------- TASK BOARD TAB ----------------

with tab_board:
    st.markdown('<div class="section-title">☷ Task board</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="muted">Update task details, change deadlines, '
        'move work forward, and mark tasks complete.</div>',
        unsafe_allow_html=True
    )

    filter_options = ["All projects"] + st.session_state.projects
    chosen_project = st.selectbox(
        "Filter by project",
        filter_options,
        key="board_project_filter"
    )

    priority_order = {"High": 0, "Medium": 1, "Low": 2}

    visible_tasks = [
        (i, item) for i, item in enumerate(st.session_state.tasks)
        if chosen_project == "All projects"
        or item.get("project", "General") == chosen_project
    ]

    visible_tasks.sort(
        key=lambda pair: (
            pair[1]["completed"],
            priority_order.get(pair[1]["priority"], 1),
            pair[0]
        )
    )

    todo_col, done_col = st.columns(2)

    with todo_col:
        st.markdown("### ◷ To do")

    with done_col:
        st.markdown("### ✓ Completed")

    todo_tasks = [(i, t) for i, t in visible_tasks if not t["completed"]]
    done_tasks = [(i, t) for i, t in visible_tasks if t["completed"]]

    with todo_col:
        if not todo_tasks:
            st.info("Nothing to do here!")
        for i, item in todo_tasks:
            with st.container(border=True):
                st.markdown(
                    f'<div class="task-title">{item["task"]}</div>',
                    unsafe_allow_html=True
                )
                st.markdown(
                    f'<span class="pill {item["priority"].lower()}">'
                    f'{item["priority"]} priority</span>',
                    unsafe_allow_html=True
                )
                st.caption(f"Project: {item.get('project', 'General')}")

                edited_date = st.date_input(
                    "Edit deadline",
                    value=item.get("due_date"),
                    key=f"edit_due_{i}"
                )
                st.session_state.tasks[i]["due_date"] = edited_date
                st.session_state.tasks[i]["deadline"] = (
                    edited_date.strftime("%d %b %Y")
                    if edited_date else "Not specified"
                )

                edited_project = st.selectbox(
                    "Project",
                    st.session_state.projects,
                    index=(
                        st.session_state.projects.index(item["project"])
                        if item.get("project") in st.session_state.projects
                        else 0
                    ),
                    key=f"edit_project_{i}"
                )
                st.session_state.tasks[i]["project"] = edited_project

                reminder_date = st.date_input(
                    "Reminder date",
                    value=item.get("reminder_date"),
                    key=f"edit_reminder_date_{i}"
                )
                st.session_state.tasks[i]["reminder_date"] = reminder_date

                reminder_time = st.time_input(
                    "Reminder time",
                    value=item.get("reminder_time") or dt.time(9, 0),
                    key=f"edit_reminder_time_{i}"
                )
                st.session_state.tasks[i]["reminder_time"] = reminder_time

                if st.button("✓ Mark complete", key=f"complete_{i}",
                             type="primary", use_container_width=True):
                    st.session_state.tasks[i]["completed"] = True
                    st.rerun()

    with done_col:
        if not done_tasks:
            st.info("Completed tasks will appear here.")
        for i, item in done_tasks:
            with st.container(border=True):
                st.markdown(f"**✓ {item['task']}**")
                st.caption(
                    f"{item['priority']} priority · "
                    f"{item.get('project', 'General')}"
                )
                if st.button(
                    "↶ Reopen task",
                    key=f"reopen_{i}",
                    use_container_width=True
                ):
                    st.session_state.tasks[i]["completed"] = False
                    st.rerun()

    if visible_tasks:
        with st.expander("Delete a task"):
            delete_options = {
                f"{item['task']} (task #{i + 1})": i
                for i, item in visible_tasks
            }
            selected_delete = st.selectbox(
                "Choose a task to delete",
                list(delete_options.keys())
            )

            if st.button("Delete selected task"):
                delete_index = delete_options[selected_delete]
                st.session_state.tasks.pop(delete_index)
                st.rerun()


# ---------------- REMINDERS TAB ----------------

with tab_reminders:
    st.markdown('<div class="section-title">◷ Reminders</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="muted">Review upcoming reminders and the dates '
        'you set for your tasks.</div>',
        unsafe_allow_html=True
    )

    reminder_tasks = []

    for item in st.session_state.tasks:
        reminder_date = item.get("reminder_date")
        due_date = item.get("due_date")

        if reminder_date or due_date:
            reminder_tasks.append(item)

    reminder_tasks.sort(
        key=lambda t: (
            t.get("reminder_date") or t.get("due_date") or today,
            t.get("reminder_time") or dt.time(9, 0)
        )
    )

    if not reminder_tasks:
        st.info(
            "No dated reminders yet. Add one when creating a task, "
            "or edit a task in the Task board tab."
        )
    else:
        for item in reminder_tasks:
            reminder_date = item.get("reminder_date")
            due_date = item.get("due_date")
            reminder_time = item.get("reminder_time") or dt.time(9, 0)

            with st.container(border=True):
                st.markdown(f"**◷ {item['task']}**")

                if reminder_date:
                    st.write(
                        f"Reminder: {reminder_date.strftime('%d %b %Y')} "
                        f"at {reminder_time.strftime('%I:%M %p')}"
                    )

                if due_date:
                    st.caption(
                        f"Deadline: {due_date.strftime('%d %b %Y')}"
                    )

                if item["completed"]:
                    st.caption("✓ Completed")
                elif reminder_date and reminder_date < today:
                    st.warning("Reminder date has passed.")
                elif due_date and due_date < today:
                    st.warning("Deadline has passed.")
                else:
                    st.caption("Upcoming")

    st.caption(
        "These are in-app reminders, not push notifications. "
        "Lumi must be open to view them."
    )

# ---------------- SAVE DATA ----------------

save_data()

# ---------------- FOOTER ----------------

st.markdown("---")
st.markdown(
    '<div style="text-align:center;color:#85849f;font-size:.8rem">'
    'LUMI · Built with Python, Streamlit & OpenRouter AI</div>',
    unsafe_allow_html=True
)
