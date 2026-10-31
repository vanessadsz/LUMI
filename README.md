# ✦ LUMI / FOLIO — Editorial AI Task Planner

**Lumi** is a quiet, high-density, AI-assisted task and project planner built with **Python**, **Streamlit**, **SQLite**, and **OpenRouter AI**, styled with the **Editorial Parchment** warm light-mode-first design system.

---

## ✦ Features

- **✧ AI Task Planner**: Describe your workload in natural language and let AI extract structured tasks with priorities (`High`, `Medium`, `Low`) and calendar deadlines.
- **⌂ Dashboard & Metrics**: Real-time overview of total, pending, completed, and upcoming tasks with completion progress tracking.
- **▦ Interactive Calendar**: Inspect tasks scheduled for any specific calendar date.
- **▧ Project Grouping**: Create custom project buckets (e.g., *College*, *Personal*, *Editorial*) with per-project progress bars.
- **☷ Two-Column Task Board**: Edit deadlines, reassign projects, set reminders, mark tasks complete, or reopen finished work.
- **◷ In-App Reminders**: Chronological view of upcoming deadlines and reminder timestamps with overdue alerts.
- **Permanent Local Storage**: Automatically persists all tasks, projects, and AI drafts in a local SQLite database (`planora.db`).

---

## ✦ Editorial Parchment Design System

Lumi implements a strict **0% pure black (`#000000`) / 0% pure white (`#FFFFFF`)** warm editorial palette:

| Token | Value | Role |
| :--- | :--- | :--- |
| **Warm Cream Beige** | `#E8D2B5` | Base application canvas |
| **Panel Surface** | `#DFC6A5` | Sidebars, segmented tab tracks, masthead |
| **Card & Input Surface** | `#F0E0C9` | Interactive cards, rows, and form controls |
| **Elevated Surface** | `#F8EEDF` | Popovers, dropdown menus, active tabs |
| **Deep Burgundy** | `#590907` | Primary ink, primary buttons, focus rings |
| **Text Emphasis** | `#3A0504` | Headlines and section titles |
| **Muted Sage Grey** | `#A5A79B` | Secondary text, metadata, full-bleed footer |

Full design specifications are documented in [`DESIGN_SYSTEM.md`](./DESIGN_SYSTEM.md) and [`DESIGN.md`](./DESIGN.md).

---

## ✦ Project Structure

```text
LUMI/
├── .streamlit/
│   ├── config.toml        # Streamlit theme configuration
│   └── secrets.toml       # Local API keys (git-ignored)
├── app.py                 # Main Streamlit application & SQLite persistence
├── style.css              # Editorial Parchment CSS token layer & component styles
├── check_models.py        # Utility script to inspect available Gemini models
├── planora.db             # Local SQLite database
├── requirements.txt       # Python dependencies
├── DESIGN.md              # Stitch design token specification
├── DESIGN_SYSTEM.md       # Master design system documentation
└── README.md              # Project documentation
```

---

## ✦ Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/vanessadsz/LUMI.git
cd LUMI
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure your API key

Create `.streamlit/secrets.toml` (or set the `OPENROUTER_API_KEY` environment variable):

```toml
OPENROUTER_API_KEY = "your-openrouter-api-key"
```

### 4. Run the application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.
