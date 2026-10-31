import os
import json
import re
import html
import datetime as dt
import requests
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
import sqlite3

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="Lumi | Editorial AI Planner",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- LOAD UI STYLES ----------------

css_file = Path(__file__).parent / "style.css"

if css_file.exists():
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
        try:
            return json.loads(row[0], object_hook=json_decode)
        except Exception:
            pass

    return {
        "tasks": [],
        "projects": ["General"],
        "ai_tasks": []
    }


# Load saved information when a Streamlit session starts.
if "storage_initialized" not in st.session_state:
    if "tasks" not in st.session_state:
        saved_data = load_data()
        st.session_state.tasks = saved_data.get("tasks", [])
        st.session_state.projects = saved_data.get("projects", ["General"])
        st.session_state.ai_tasks = saved_data.get("ai_tasks", [])
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
    if 0 <= index < len(st.session_state.tasks) and key in st.session_state:
        st.session_state.tasks[index]["completed"] = st.session_state[key]
        save_data()


# ---------------- AI INTEGRATION ----------------

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openrouter/free"


def get_openrouter_api_key():
    """Retrieve OpenRouter API key from Streamlit secrets or environment variables."""
    try:
        key = st.secrets.get("OPENROUTER_API_KEY")
        if key:
            return str(key).strip()
    except Exception:
        pass
    return os.environ.get("OPENROUTER_API_KEY", "").strip()


def organize_tasks(description):
    api_key = get_openrouter_api_key()
    if not api_key:
        raise RuntimeError(
            "Missing OPENROUTER_API_KEY. Add it to .streamlit/secrets.toml "
            "or set it as an environment variable."
        )

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

    payload = response.json()
    choices = payload.get("choices") or []
    if not choices or "message" not in choices[0]:
        raise RuntimeError("Unexpected response format from OpenRouter.")

    content = (choices[0]["message"].get("content") or "").strip()
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", content, flags=re.DOTALL)
        if not match:
            raise ValueError("Could not parse JSON task list from AI response.")
        result = json.loads(match.group(0))

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

st.markdown("""
<div class="brand">
    <div class="brand-left">
        <span class="brand-mark">✦</span>
        <span>LUMI</span>
        <span style="color:#A5A79B;font-size:15px;font-weight:550;margin-left:6px">
            AI PRODUCTIVITY WORKSPACE
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------- TERMINAL SPLIT-FLAP BOARD (rustedpotato/UI-UX) ----------------

FLIP_BOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;700&display=swap');

  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }

  html, body {
    width: 100%;
    background: transparent;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #590907;
    padding: 4px 2px 16px;
  }

  .terminal-wrapper {
    width: 100%;
    max-width: 100%;
    margin: 0 auto;
    border-radius: 12px;
    border: 1px solid rgba(89, 9, 7, 0.20);
    background: #DFC6A5;
    padding: 16px 20px 20px;
    box-shadow: inset 0 1px 0 rgba(248, 238, 223, 0.75), 0 8px 20px rgba(89, 9, 7, 0.12);
  }

  .terminal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid rgba(89, 9, 7, 0.16);
    padding-bottom: 10px;
    margin-bottom: 14px;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #590907;
  }

  .terminal-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
  }

  .terminal-btn {
    cursor: pointer;
    border-radius: 6px;
    border: 1px solid rgba(89, 9, 7, 0.26);
    background: #F0E0C9;
    color: #590907;
    padding: 6px 14px;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 13px;
    font-weight: 600;
    transition: background-color 120ms ease, transform 80ms ease;
  }

  .terminal-btn:hover {
    background: #E4CDAE;
  }

  .terminal-btn:active {
    transform: scale(0.96);
  }

  .board-frame {
    position: relative;
    width: 100%;
    border-radius: 10px;
    background: #F8EEDF;
    border: 1px solid rgba(89, 9, 7, 0.16);
    padding: 12px;
    box-shadow: inset 0 1px 2px rgba(89, 9, 7, 0.08);
  }

  .board-grid {
    display: grid;
    grid-template-columns: repeat(22, minmax(0, 1fr));
    gap: 3px;
  }

  .flap-cell {
    display: flex;
    flex-direction: column;
    height: 46px;
    overflow: hidden;
    border-radius: 3px;
    border: 1.5px solid rgba(89, 9, 7, 0.22);
    background: #F0E0C9;
  }

  .flap-stage {
    position: relative;
    flex: 1;
    perspective: 300px;
    transform-style: preserve-3d;
  }

  .flap-half {
    position: absolute;
    left: 0;
    right: 0;
    height: calc(50% - 0.5px);
    overflow: hidden;
    background: #F0E0C9;
    color: #3A0504;
  }

  .flap-top {
    top: 0;
    border-top-left-radius: 2px;
    border-top-right-radius: 2px;
  }

  .flap-bottom {
    bottom: 0;
    border-bottom-left-radius: 2px;
    border-bottom-right-radius: 2px;
  }

  .flap-char {
    position: absolute;
    left: 0;
    right: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-weight: 700;
    font-size: clamp(12px, 1.75vw, 20px);
    line-height: 1;
    user-select: none;
    height: 200%;
  }

  .flap-top .flap-char {
    top: 0;
  }

  .flap-bottom .flap-char {
    bottom: 0;
  }

  .split-line {
    pointer-events: none;
    position: absolute;
    left: 0;
    right: 0;
    top: 50%;
    height: 1px;
    transform: translateY(-0.5px);
    background: rgba(89, 9, 7, 0.28);
    z-index: 20;
  }

  .flap-stripes {
    height: 5px;
    width: 100%;
    background: repeating-linear-gradient(
      to bottom,
      rgba(89, 9, 7, 0.20) 0,
      rgba(89, 9, 7, 0.20) 1px,
      transparent 1px,
      transparent 2.5px
    );
  }

  /* Accent flash colors during scramble */
  .accent-burgundy .flap-half { background: #590907; color: #E8D2B5; }
  .accent-sage .flap-half     { background: #A5A79B; color: #3A0504; }
  .accent-gold .flap-half     { background: #9A6A12; color: #F8EEDF; }
  .accent-crimson .flap-half  { background: #B3261E; color: #F8EEDF; }
  .accent-forest .flap-half   { background: #4F6B3A; color: #F8EEDF; }

  @keyframes flipPulse {
    0%   { transform: rotateX(0deg); filter: brightness(0.92); }
    50%  { transform: rotateX(-65deg); filter: brightness(0.82); }
    100% { transform: rotateX(0deg); filter: brightness(1); }
  }

  .flipping .flap-stage {
    animation: flipPulse 110ms cubic-bezier(0.25, 0.46, 0.45, 0.94);
  }
</style>
</head>
<body>
  <div class="terminal-wrapper">
    <div class="terminal-header">
      <span class="terminal-title">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>
        </svg>
        TERMINAL 01 // LUMI DISPATCH &amp; FOCUS
      </span>
      <button id="nextBtn" class="terminal-btn" type="button">
        Next Message (1/4)
      </button>
    </div>
    <div class="board-frame">
      <div id="boardGrid" class="board-grid"></div>
    </div>
  </div>

<script>
  const FLAP_CHARS = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$()-+&=;:'\\"%,./?";
  const BOARD_ROWS = 6;
  const BOARD_COLS = 22;
  const BASE_COL_DELAY = 26;
  const BASE_ROW_DELAY = 18;
  const STEP_MS = 48;

  const MESSAGES = [
    "MAKE ROOM FOR\\nWHAT MATTERS\\n- LUMI PLANNER",
    "ORGANIZE TASKS\\nTRACK DEADLINES\\nSTAY IN FLOW",
    "QUIET CLARITY\\nHIGH DENSITY\\nZERO DISTRACTION",
    "PLAN YOUR DAY\\nBUILD MOMENTUM\\nSHIP YOUR WORK"
  ];

  const ACCENTS = [
    "accent-burgundy",
    "accent-sage",
    "accent-gold",
    "accent-crimson",
    "accent-forest"
  ];

  const gridEl = document.getElementById("boardGrid");
  const nextBtn = document.getElementById("nextBtn");
  let msgIdx = 0;

  // Build 6x22 DOM cells
  const cells = [];
  for (let r = 0; r < BOARD_ROWS; r++) {
    cells[r] = [];
    for (let c = 0; c < BOARD_COLS; c++) {
      const cellEl = document.createElement("div");
      cellEl.className = "flap-cell";
      cellEl.innerHTML = `
        <div class="flap-stage">
          <div class="flap-half flap-top"><div class="flap-char">&nbsp;</div></div>
          <div class="flap-half flap-bottom"><div class="flap-char">&nbsp;</div></div>
          <div class="split-line"></div>
        </div>
        <div class="flap-stripes"></div>
      `;
      gridEl.appendChild(cellEl);
      const charEls = cellEl.querySelectorAll(".flap-char");
      cells[r][c] = {
        el: cellEl,
        topChar: charEls[0],
        botChar: charEls[1],
        current: " ",
        target: " ",
        startTimer: null,
        stepTimer: null
      };
    }
  }

  function wrapParagraph(paragraph, maxCols) {
    const lines = [];
    const words = paragraph.split(/[ \\t]+/).filter(Boolean);
    let currentLine = "";
    for (const word of words) {
      if (word.length > maxCols) {
        if (currentLine) { lines.push(currentLine); currentLine = ""; }
        lines.push(word.slice(0, maxCols));
        continue;
      }
      if (!currentLine) {
        currentLine = word;
      } else if (currentLine.length + 1 + word.length <= maxCols) {
        currentLine += " " + word;
      } else {
        lines.push(currentLine);
        currentLine = word;
      }
    }
    if (currentLine) lines.push(currentLine);
    return lines;
  }

  function buildBoardMatrix(text) {
    const matrix = Array.from({ length: BOARD_ROWS }, () =>
      Array.from({ length: BOARD_COLS }, () => " ")
    );
    const rawLines = text.split("\\n").flatMap(p =>
      p.trim() === "" ? [""] : wrapParagraph(p, BOARD_COLS)
    ).slice(0, BOARD_ROWS);

    const startRow = Math.max(0, Math.floor((BOARD_ROWS - rawLines.length) / 2));
    rawLines.forEach((line, i) => {
      const r = startRow + i;
      if (r >= BOARD_ROWS) return;
      const startCol = Math.max(0, Math.floor((BOARD_COLS - line.length) / 2));
      for (let c = 0; c < line.length; c++) {
        if (startCol + c < BOARD_COLS) {
          matrix[r][startCol + c] = line[c].toUpperCase();
        }
      }
    });
    return matrix;
  }

  function setCellChar(cell, ch, accentClass) {
    cell.current = ch;
    const display = ch === " " ? "\\u00A0" : ch;
    cell.topChar.textContent = display;
    cell.botChar.textContent = display;
    cell.el.className = "flap-cell flipping" + (accentClass ? " " + accentClass : "");
    setTimeout(() => {
      cell.el.classList.remove("flipping");
    }, 95);
  }

  function animateCell(cell, targetChar, delay) {
    if (cell.startTimer) clearTimeout(cell.startTimer);
    if (cell.stepTimer) clearTimeout(cell.stepTimer);

    const normalized = FLAP_CHARS.includes(targetChar) ? targetChar : " ";
    if (normalized === cell.current && normalized === " ") return;

    const scrambleCount = normalized === " "
      ? 6 + Math.floor(Math.random() * 6)
      : 14 + Math.floor(Math.random() * 10);

    const runStep = (step) => {
      const isLast = step >= scrambleCount;
      const ch = isLast
        ? normalized
        : FLAP_CHARS[1 + Math.floor(Math.random() * (FLAP_CHARS.length - 1))];
      const accent = (!isLast && Math.random() < 0.22)
        ? ACCENTS[Math.floor(Math.random() * ACCENTS.length)]
        : "";
      setCellChar(cell, ch, accent);
      if (!isLast) {
        cell.stepTimer = setTimeout(() => runStep(step + 1), STEP_MS);
      }
    };

    cell.startTimer = setTimeout(() => runStep(1), delay);
  }

  function renderMessage(index) {
    const matrix = buildBoardMatrix(MESSAGES[index]);
    nextBtn.textContent = `Next Message (${index + 1}/${MESSAGES.length})`;
    for (let r = 0; r < BOARD_ROWS; r++) {
      for (let c = 0; c < BOARD_COLS; c++) {
        const delay = c * BASE_COL_DELAY + r * BASE_ROW_DELAY;
        animateCell(cells[r][c], matrix[r][c], delay);
      }
    }
  }

  function nextMessage() {
    msgIdx = (msgIdx + 1) % MESSAGES.length;
    renderMessage(msgIdx);
  }

  nextBtn.addEventListener("click", () => {
    nextMessage();
    resetAutoTimer();
  });

  let autoTimer = setInterval(nextMessage, 6500);
  function resetAutoTimer() {
    clearInterval(autoTimer);
    autoTimer = setInterval(nextMessage, 6500);
  }

  renderMessage(0);
</script>
</body>
</html>
"""

components.html(FLIP_BOARD_HTML, height=415, scrolling=False)


# ---------------- DASHBOARD METRICS ----------------

tasks = st.session_state.tasks
total = len(tasks)
completed_count = sum(bool(t.get("completed")) for t in tasks)
pending_count = total - completed_count
today = dt.date.today()

upcoming_count = sum(
    isinstance(t.get("due_date"), dt.date)
    and t["due_date"] >= today
    and not t.get("completed")
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


# ---------------- THREE-COLUMN APP SHELL ----------------
# Left: Navigation Rail | Middle: Active View (AI Planner & Plans) | Right: Your Tasks

NAV_ITEMS = [
    "⌂  Dashboard",
    "▦  Calendar",
    "▧  Projects",
    "☷  Task board",
    "◷  Reminders"
]

st.session_state.setdefault("active_nav", NAV_ITEMS[0])

left_nav_col, center_main_col, right_task_col = st.columns(
    [1.15, 2.55, 1.65],
    gap="medium"
)

# ---------------- LEFT COLUMN: NAVIGATION ----------------
with left_nav_col:
    with st.container(border=True):
        st.markdown(
            '<div class="nav-group-header">WORKSPACE VIEWS</div>',
            unsafe_allow_html=True
        )
        for nav_label in NAV_ITEMS:
            is_active = (st.session_state.active_nav == nav_label)
            if st.button(
                nav_label,
                key=f"nav_btn_{nav_label}",
                type="primary" if is_active else "secondary",
                width="stretch"
            ):
                st.session_state.active_nav = nav_label
                st.rerun()

# ---------------- MIDDLE COLUMN: AI PLANNER, PLANS & VIEWS ----------------
with center_main_col:
    active_view = st.session_state.active_nav

    # -------- VIEW 1: DASHBOARD (ORGANIZE WITH AI, PLANS & QUICK ADD) --------
    if active_view == "⌂  Dashboard":
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
                    width="stretch"
                )

            if ai_submit:
                if not description.strip():
                    st.warning("Describe your tasks first.")
                else:
                    try:
                        with st.spinner("AI is planning your tasks..."):
                            st.session_state.ai_tasks = organize_tasks(description)
                        save_data()
                        st.rerun()
                    except Exception as e:
                        st.error("The AI request failed.")
                        st.caption(str(e))

        st.markdown('<div class="section-title">✦ Your AI plans</div>',
                    unsafe_allow_html=True)

        if st.session_state.ai_tasks:
            for n, item in enumerate(st.session_state.ai_tasks, start=1):
                with st.container(border=True):
                    st.markdown(f"**{n}. {item['task']}**")
                    priority_label = html.escape(str(item.get("priority", "Medium")))
                    deadline_label = html.escape(str(item.get("deadline", "Not specified")))
                    st.markdown(
                        f'<span class="pill {priority_label.lower()}">'
                        f'{priority_label} priority</span>',
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        f'<div class="muted">Deadline: {deadline_label}</div>',
                        unsafe_allow_html=True
                    )

            if st.button("＋ Add AI tasks to my list",
                         type="primary", width="stretch"):
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
                save_data()
                st.toast(f"Added {added} task(s)!")
                st.rerun()
        else:
            with st.container(border=True):
                st.caption(
                    "Your AI-organized plan will appear here once you describe "
                    "your workload above and click '✦ Organize with AI'."
                )

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
                    width="stretch"
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
                    save_data()
                    st.toast("Task added!")
                    st.rerun()

    # -------- VIEW 2: CALENDAR --------
    elif active_view == "▦  Calendar":
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
                        f"{'Completed' if item.get('completed') else 'To do'}"
                    )
        else:
            st.info("No tasks with an editable calendar date on this day.")

        st.caption(
            "Tasks with only a text deadline, such as 'sometime next week', "
            "appear here once you assign them a calendar date in the task board."
        )

    # -------- VIEW 3: PROJECTS --------
    elif active_view == "▧  Projects":
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
                    width="stretch"
                )

            if project_submit:
                clean_name = project_name.strip()
                if clean_name and clean_name not in st.session_state.projects:
                    st.session_state.projects.append(clean_name)
                    save_data()
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
            project_done = sum(bool(t.get("completed")) for t in project_tasks)

            with st.container(border=True):
                st.markdown(f"**▧ {project}**")
                st.caption(
                    f"{len(project_tasks)} tasks · {project_done} completed"
                )
                if project_tasks:
                    st.progress(project_done / len(project_tasks))

                    for item in project_tasks:
                        st.write(
                            f"{'✓' if item.get('completed') else '○'} "
                            f"{item['task']}"
                        )

    # -------- VIEW 4: TASK BOARD --------
    elif active_view == "☷  Task board":
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
                pair[1].get("completed", False),
                priority_order.get(pair[1].get("priority", "Medium"), 1),
                pair[0]
            )
        )

        todo_col, done_col = st.columns(2)

        with todo_col:
            st.markdown("### ◷ To do")

        with done_col:
            st.markdown("### ✓ Completed")

        todo_tasks = [(i, t) for i, t in visible_tasks if not t.get("completed")]
        done_tasks = [(i, t) for i, t in visible_tasks if t.get("completed")]

        with todo_col:
            if not todo_tasks:
                st.info("Nothing to do here!")
            for i, item in todo_tasks:
                with st.container(border=True):
                    safe_title = html.escape(str(item["task"]))
                    priority_label = html.escape(str(item.get("priority", "Medium")))
                    st.markdown(
                        f'<div class="task-title">{safe_title}</div>',
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        f'<span class="pill {priority_label.lower()}">'
                        f'{priority_label} priority</span>',
                        unsafe_allow_html=True
                    )
                    st.caption(f"Project: {item.get('project', 'General')}")

                    edited_date = st.date_input(
                        "Edit deadline",
                        value=item.get("due_date"),
                        key=f"edit_due_{i}"
                    )
                    st.session_state.tasks[i]["due_date"] = edited_date
                    if edited_date:
                        st.session_state.tasks[i]["deadline"] = edited_date.strftime("%d %b %Y")
                    elif isinstance(item.get("due_date"), dt.date):
                        st.session_state.tasks[i]["deadline"] = "Not specified"

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
                                 type="primary", width="stretch"):
                        st.session_state.tasks[i]["completed"] = True
                        save_data()
                        st.rerun()

        with done_col:
            if not done_tasks:
                st.info("Completed tasks will appear here.")
            for i, item in done_tasks:
                with st.container(border=True):
                    st.markdown(f"**✓ {item['task']}**")
                    st.caption(
                        f"{item.get('priority', 'Medium')} priority · "
                        f"{item.get('project', 'General')}"
                    )
                    if st.button(
                        "↶ Reopen task",
                        key=f"reopen_{i}",
                        width="stretch"
                    ):
                        st.session_state.tasks[i]["completed"] = False
                        save_data()
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
                    for k in list(st.session_state.keys()):
                        if k.startswith((
                            "edit_due_",
                            "edit_project_",
                            "edit_reminder_date_",
                            "edit_reminder_time_",
                            "dashboard_done_",
                        )):
                            del st.session_state[k]
                    save_data()
                    st.rerun()

    # -------- VIEW 5: REMINDERS --------
    elif active_view == "◷  Reminders":
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

                    if item.get("completed"):
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

# ---------------- RIGHT COLUMN: YOUR TASK LIST & DAY AT A GLANCE ----------------
with right_task_col:
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
                col_task, col_check = st.columns([4, 1.3])

                with col_task:
                    st.markdown(f"**{item['task']}**")
                    priority_label = html.escape(str(item.get("priority", "Medium")))
                    st.markdown(
                        f'<span class="pill {priority_label.lower()}">'
                        f'{priority_label} priority</span>',
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

    st.markdown('<div class="section-title">◷ Your day at a glance</div>',
                unsafe_allow_html=True)

    todays_tasks = [
        t for t in st.session_state.tasks
        if t.get("due_date") == today and not t.get("completed")
    ]

    if todays_tasks:
        with st.container(border=True):
            for item in todays_tasks:
                st.write(f"◷ **{item['task']}** · {item['priority']}")
    else:
        st.info("Nothing is due today, or no dated tasks have been added yet.")


# ---------------- SAVE DATA ----------------

save_data()

# ---------------- FOOTER ----------------

st.markdown("""
<div class="ep-footer">
    <div class="ep-footer-title">✦ LUMI</div>
</div>
""", unsafe_allow_html=True)
