# 🪐 Orbit — Your Personal Academic Companion

> *"Plan your day around you."*

Orbit is an AI-powered student companion that plans your day around your mood,
energy, and goals — so academics, habits, and well-being all stay in balance.

Built solo for the **DA-IICT AI Club Buildathon 2026** by a first-year student,
for students.

---

## 📌 Problem Statement

College students juggle academics, deadlines, club commitments, personal goals,
and their own mental and physical well-being — all at once. Yet every tool they
use treats these as separate problems.

- Google Calendar manages time but doesn't know you're exhausted
- Notion tracks tasks but doesn't care that you slept 4 hours
- Attendance apps calculate percentages but don't warn you before it's too late
- No app notices when you've been struggling for a week and adjusts accordingly

No existing tool connects **how you feel** with **what you need to do** to give
you a plan that actually works for you — today, not in general.

**Orbit solves this** by combining a student's timetable, tasks, recurring goals,
sleep, and mood into one AI-generated personalized daily plan — that adapts to
how they're actually feeling, not how they planned to feel.

---

## ✅ Current Progress

- [x] Project setup — virtual environment, dependencies installed
- [x] Database layer — SQLite with 9 tables
  - timetable, tasks, goals, daily_logs, attendance,
    holidays, semester, streaks, rewards
- [x] Home page — daily mood + sleep check-in, live quick stats, AI day plan
- [x] Timetable page — add subjects, class timings, semester dates, holidays
- [x] Tasks page — add tasks with priority, tick off, delete, pie chart
- [x] Attendance page — mark attendance, auto-calculate %, bunk calculator
- [x] Goals page — recurring habits, streak tracker, milestone display
- [x] Rewards page — unlockable rewards based on streak milestones
- [x] AI layer — Groq API (Llama 3.3 70B) generates personalized day plan
- [x] Mood pattern detection — lighter plan + support nudge after 5 low days
- [x] Overwhelmed button — regenerates a lighter, kinder plan on demand
- [x] Bunk calculator — smart attendance math using timetable + semester dates
- [x] Weekly summary — productivity trends and pattern insights
- [x] Streamlit Cloud deployment

---

## 🛠️ Tech Stack

| Layer | Tool |
|---|---|
| Frontend | Streamlit |
| Backend | Python |
| Database | SQLite (orbit.db) |
| AI Model | Groq API — Llama 3.3 70B |
| Hosting | Streamlit Community Cloud |

---

## 📁 Project Structure

```
Orbit/
├──app.py
├── home.py                 # Home page — check-in + AI day plan
├──backend
│     └── database.py       # SQLite setup, connection, all 9 tables
├──frontend
│     └──styling.py         # Styling in css
├── key.md                  # Groq API key (never pushed to GitHub)
├── .onboarding             #first-time user
├── .gitignore              # Excludes key.md, orbit.db, venv, pycache
├── ai/
│   └── service.py          # Groq API call, prompt logic, mood pattern detection
└── pages/
    ├── 1_Goals.py          
    ├── 2_Notes.py         
    ├── 3_Rewards.py        
    ├── 4_Tasks.py          
    └── 5_Timetable.py  
    └── 6_Analysis.py 
    └── 7_Profile.py 
    └── 8_Logout.py       
```

---

## 🎯 Features

### Have ✅
- Daily mood + sleep check-in powering an AI-generated day plan
- Task and deadline logger with priority levels
- Attendance tracker with 75% rule calculator and early warnings
- Recurring personal goals manager (e.g. 10 DSA questions daily)
- Bunk calculator — tells you exactly how many classes you can safely miss
- Weekly pattern summary and productivity trends
- Club and extracurricular time blocking
- Mnaula adjustmensts of timetable
- AIchatbot assistance for better scheduling or comfort
- logput and profile pages
- managing data(deleting history)
- Seperate page for you to add manual tasks
- option to tighten or relax your plan

### Nice to Have
- Cycle-aware scheduling (optional well-being toggle)
- Stress spike detection around exam periods
- Multi-day planning view (week ahead)
- Course syllabus upload — AI maps topics to exam deadlines

---

## 🤖 How the AI Works

Orbit's AI layer (Groq + Llama 3.3 70B) receives the student's full personal
context on every check-in:

- Today's mood and sleep hours
- Pending tasks sorted by deadline
- Today's class schedule from timetable
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

## ⚙️ Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/bhagy-shr/Orbit.git
cd Orbit
```

### 2. Create and activate virtual environment

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

Create a file called `key.md` in the root folder:
```
GROQ_API_KEY=your_api_key_here
```

Get your free API key at [console.groq.com](https://console.groq.com)

### 5. Run the app
```bash
streamlit run app.py
```

The app opens automatically at `http://localhost:8501`

---

## ⚠️ Important Notes

- Never push `key.md` or `orbit.db` to GitHub — both are in `.gitignore`
- Set up your timetable and semester dates first before using other features
- The AI day plan generates fresh on each check-in

---

## 💙 Why Orbit is Different

| Tool | What it does | What it misses |
|---|---|---|
| Google Calendar | Time blocking | Doesn't know your energy or mood |
| Notion / Todoist | Task management | No student-specific context |
| Attendance apps | Tracks % | Doesn't connect to your full schedule |
| Generic well-being apps | Mood logging | No connection to academics |

**Orbit is the only tool that combines attendance + tasks + goals + mood + sleep
into a single AI-generated daily plan that adapts to how you're actually feeling.**

---

## 👩‍💻 Built By

**Bhagyashree** — First Year B.Tech ICT-CS, DA-IICT
Built solo for the DA-IICT AI Club Buildathon 2026

*"Built by a student, for students."*