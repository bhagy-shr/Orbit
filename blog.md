# Building Orbit: My Journey Creating the Ultimate Student Academic AI Companion

Welcome to the story of **Orbit**—a smart, personalized academic companion designed to help students manage schedules, track habits, stay on top of class attendance, and navigate the daily hustle without burning out.

This is the journey of how Orbit evolved from a basic LLM prompt generator into a deterministic, timezone-aware, and clash-resistant productivity ecosystem.

---

## 🪐 The Vision Behind Orbit
Most calendar and planner apps are static, demanding, and insensitive to student energy. They don't care if you slept for only 4 hours or if you are feeling completely overwhelmed. 

Our goal for Orbit was to create an AI companion that:
1. **Calibrates to your energy**: Adjusts schedule density based on sleep and mood.
2. **Keeps your calendar realistic**: Prevents tasks from bleeding into bedtime.
3. **Supports you when overwhelmed**: Drops low-priority tasks and suggests half-time adjustments when you are struggling.
4. **Keeps class standings secure**: Generates critical bunk warnings if attendance drops below 75%.

---

## 🛠️ The Tech Stack
* **Frontend**: [Streamlit](https://streamlit.io/) for a rapid, sleek, and responsive user interface.
* **Database**: [SQLite3](https://www.sqlite.org/) for lightweight, persistent local storage.
* **AI Engine**: [Groq API](https://groq.com/) utilizing the `llama-3.1-8b-instant` model for writing friendly check-ins, motivation quotes, and smart comments.

---

## 🚀 Key Challenges & Technical Breakthroughs

### 1. Taming the LLM: Reining in Task Hallucinations
In the beginning, we relied on the LLM to write the calendar layout. However, LLMs consistently struggled with time boundaries, duration math, and scheduling. It would hallucinate tasks (like adding "DSA Midterm study" when the user hadn't even added it to the database) or skip meals.

* **The Fix**: We stripped the LLM of its calendar-creation powers. We wrote a **deterministic Python calendar scheduler** based on 30-minute relative slots starting from the user's wake-up time. The LLM's role was reduced to doing what it does best: writing friendly daily check-ins, motivation quotes, and context-aware suggestions.

### 2. Timezone Date Lag: Solving the "Stuck Date" Problem
When running Orbit on a cloud server, the system local time is typically locked to UTC. This created a frustrating lag—for example, it would show the date as **June 19th** even though it was already **June 20th** in the user's timezone.

* **The Fix**: We upgraded the database to store a user-specific `timezone_offset` (defaulting to IST, `+05:30`). We implemented custom timezone helpers:
  ```python
  def get_local_now():
      offset = get_user_timezone_offset()
      return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=offset)
  ```
  We replaced `datetime.date.today()` globally with `get_local_today()`, syncing the entire application's date metrics to the student's actual physical location.

### 3. Bulletproof Bedtime & 24-Hour Routine Transitions
Initially, a user waking up at 5:00 AM and sleeping at 9:00 PM would find tasks scheduled past midnight.
* **The Fix**: We transitioned all profile settings (waking, sleeping, and meal times) to a strict **24-hour dropdown selector**. The scheduler calculates relative offsets relative to midnight crossings, strictly truncating the day plan at the student's chosen bedtime.

### 4. Resilient Clash Handling: Stacking & The Active Study Window
What happens when you have a class, a meal, and a high-priority assignment due at the same hour?
* **The Fix**: We implemented **Slot Stacking**. Instead of failing to schedule or dropping clashing tasks, the calendar combines them:
  `09:00 - 10:00 — 🔴 DSA Homework / 🔴 Chemistry clash`
* If unscheduled tasks run out of empty slots, they automatically target the student's preferred focus window (e.g. **Morning Focus**, **Evening Focus**) and stack within those slots, keeping all commitments visible.

### 5. Overwhelmed Mode & Simplify Plan
When a student feels down, they need rest. Orbit provides a "Simplify Plan" button that:
* Wipes out all Low Priority (`🟡`) tasks from the schedule.
* Triggers a dialog allowing the student to quickly halve study hours or delete them.
* Programmatically reminds them: *"You have high-priority tasks today. If you are struggling with time, please adjust your timetable manually to decide which tasks you would like to compromise time on."*

---

## 📈 Lessons Learned
1. **Algorithmic Guardrails are Essential**: AI is great for text generation, but business logic, calendars, and schedules must remain deterministic. Combining Python time calculations with LLM commentary gave us the best of both worlds.
2. **Edge Cases Matter**: Time routines are personal. Handling sleep offsets, midnight crossings, and variable timezones required meticulous unit testing.
3. **Clean Code Structures Save Time**: A misplaced code block or nested import can crash the entire application layout. Keeping functions clean, decoupled, and modular is key to maintaining a production-ready application.

---

## 🌟 What's Next for Orbit?
Orbit is now fully synced, committed, and deployed. In the future, we plan to add:
* **Interactive charts** to visualize mood and sleep correlations.
* **Real-time calendar integrations** (like Google Calendar API).
* **Pomodoro session integrations** to track actual focus blocks directly in the app.

Orbit is more than a scheduler; it's a supportive friend in a student's pocket. Here's to making academic lives a little less overwhelming! 🪐✨
