# 🪐 Orbit — Your Personal Academic Companion

> *"Plan your day around you."*

Orbit is an AI-powered student companion that plans your day around your mood, energy, and goals — so academics, habits, and well-being stay in balance instead of competing with each other.

Built solo for the **DA-IICT AI Club Buildathon 2026** by a first-year student, for students.

**🔗 Live app:** [orbit-companion.streamlit.app](https://orbit-companion.streamlit.app/)
**💻 Source:** [github.com/bhagy-shr/Orbit](https://github.com/bhagy-shr/Orbit)

---

## 📌 Problem statement

College students juggle academics, deadlines, club commitments, personal goals, and their own mental and physical well-being — all at once. Yet every tool they use treats these as separate problems.

- Google Calendar manages time but doesn't know you're exhausted.
- Notion tracks tasks but doesn't care that you slept 4 hours.
- Attendance apps calculate percentages but don't warn you before it's too late.
- No app notices when you've been struggling for a week and adjusts accordingly.

No existing tool connects **how you feel** with **what you need to do** to give you a plan that actually works for you — today, not in general.

**Orbit solves this** by combining a student's timetable, tasks, recurring goals, sleep, and mood into one AI-generated daily plan that adapts to how they're actually feeling, not how they planned to feel.

---

## 🛠️ Tech stack

| Layer | Tool |
|---|---|
| Frontend | Streamlit |
| Backend | Python |
| Database | SQLite (`orbit.db`) |
| AI model | Groq API — Llama 3.3 70B |
| Charts | Plotly |
| Hosting | Streamlit Community Cloud |

---

## 🎯 What Orbit does

### Core features
- **Daily check-in** — logs mood and sleep hours, feeds directly into the AI-generated day plan.
- **AI day planner** — generates a personalized hour-by-hour plan using Groq/Llama 3.3 70B, grounded in the student's real schedule, tasks, and state.
- **Task & deadline logger** — add tasks with priority levels, tick off or delete, visualized with a completion pie chart.
- **Timetable management** — add subjects, class timings, semester dates, and holidays; manually adjust the timetable when needed.
- **Attendance tracker** — auto-calculates attendance percentage per subject, with 75%-rule warnings before it's too late.
- **Bunk calculator** — tells you exactly how many classes you can safely miss without dropping below the cutoff, using your real timetable and semester dates.
- **Recurring goals & streaks** — track habitual goals (e.g. "10 DSA questions daily"), with streak tracking and milestone display.
- **Rewards system** — unlockable rewards tied to streak milestones.
- **Notes page** — a dedicated space for adding and keeping notes.
- **Weekly summary** — surfaces productivity trends and pattern insights over the week.
- **AI chatbot assistance** — conversational help for scheduling or general comfort/support.
- **Profile & data management** — view/edit profile, delete history, log out.
- **Adjustable plan intensity** — tighten or relax your plan on demand.

### Nice to have (future)
- Cycle-aware scheduling (optional well-being toggle)
- Stress spike detection around exam periods
- Multi-day planning view (week ahead)
- Course syllabus upload — AI maps topics to exam deadlines

---

## 🤖 How the AI works

Orbit's AI layer (Groq + Llama 3.3 70B) receives the student's full personal context on every check-in:

- Today's mood and sleep hours
- Pending tasks, sorted by deadline
- Today's class schedule from the timetable
- Recurring goals and targets
- Attendance warnings (subjects below 75%)
- Mood history from the last 7 days

It then generates one of three types of responses:

| Situation | Response |
|---|---|
| Normal day | Personalized hour-by-hour plan |
| Student clicks "This feels like too much" | Lighter plan, one priority only, permission to skip |
| Low mood for 5+ days detected | Care-first response, gentle nudge to talk to someone |

---

## 📁 Project structure

```
Orbit/
├── app.py
├── home.py                 # Home page — check-in + AI day plan
├── backend/
│   └── database.py         # SQLite setup, connection, all 9 tables
├── frontend/
│   └── styling.py           # CSS styling
├── ai/
│   └── service.py            # Groq API calls, prompt logic, mood pattern detection
├── pages/
│   ├── 1_Goals.py
│   ├── 2_Notes.py
│   ├── 3_Rewards.py
│   ├── 4_Tasks.py
│   ├── 5_Timetable.py
│   ├── 6_Analysis.py
│   ├── 7_Profile.py
│   └── 8_Logout.py
├── key.md                   # Groq API key (never pushed to GitHub)
├── .onboarding                # First-time user flow
└── .gitignore                 # Excludes key.md, orbit.db, venv, __pycache__
```

**Database layer:** SQLite with 9 tables — `timetable`, `tasks`, `goals`, `daily_logs`, `attendance`, `holidays`, `semester`, `streaks`, `rewards`.

---

## ⚙️ Setup instructions

### 1. Clone the repository
```bash
git clone https://github.com/bhagy-shr/Orbit.git
cd Orbit
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
```

**Windows:**
```bash
.\venv\Scripts\Activate.ps1
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install streamlit groq plotly
```

### 4. Set up your Groq API key

Create a file called `KEY.md` in the root folder:
```
GROQ_API_KEY=your_api_key_here
```

Get a free API key at [console.groq.com](https://console.groq.com).

### 5. Run the app
```bash
streamlit run app.py
```

The app opens automatically at `http://localhost:8501`.

---

## ⚠️ Important notes

- Never push `key.md` or `orbit.db` to GitHub — both are excluded via `.gitignore`.
- Set up your timetable and semester dates first before using other features.
- The AI day plan regenerates fresh on every check-in.

---

## 💙 Why Orbit is different

| Tool | What it does | What it misses |
|---|---|---|
| Google Calendar | Time blocking | Doesn't know your energy or mood |
| Notion / Todoist | Task management | No student-specific context |
| Attendance apps | Tracks percentage | Doesn't connect to your full schedule |
| Generic well-being apps | Mood logging | No connection to academics |

**Orbit is the only tool that combines attendance, tasks, goals, mood, and sleep into a single AI-generated daily plan that adapts to how you're actually feeling.**

---

## 👩‍💻 Built by

**Bhagyashree** — First Year B.Tech ICT-CS, DA-IICT
Built solo for the DA-IICT AI Club Buildathon 2026

*"Built by a student, for students."*