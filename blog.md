# Building Orbit: My Journey Creating a Student Academic AI Companion

**Orbit** is a smart, personalized academic companion built to help students manage schedules, track habits, stay on top of attendance, and get through the daily hustle without burning out. This is the story of how it evolved from a basic LLM prompt generator into a deterministic, timezone-aware, clash-resistant productivity tool.

---

## 🪐 The vision

Most planner apps are static and insensitive to student energy — they don't care if you slept 4 hours or feel completely overwhelmed. Orbit was built to:

1. **Calibrate to your energy** — adjust schedule density based on sleep and mood.
2. **Keep your calendar realistic** — prevent tasks from bleeding into bedtime.
3. **Support you when overwhelmed** — drop low-priority tasks, suggest half-time adjustments.
4. **Protect your class standing** — warn before attendance drops below 75%.

---

## 🛠️ Tech stack

- **Frontend**: [Streamlit](https://streamlit.io/)
- **Database**: [SQLite3](https://www.sqlite.org/)
- **AI engine**: [Groq API](https://groq.com/) — `llama-3.1-8b-instant`, for check-ins, motivation, and context-aware comments

---

## 🚀 Key challenges

**1. Taming the LLM's hallucinations**
The LLM originally wrote the calendar directly — and consistently hallucinated tasks that were never added, or botched time/duration math. Fix: strip the LLM of calendar-building entirely. A deterministic Python scheduler now builds the day in 30-minute slots from wake-up time; the LLM's job is reduced to what it's actually good at — friendly commentary, not scheduling logic.

**2. The "stuck date" problem**
On a cloud server locked to UTC, the app would show June 19th when it was already June 20th locally. Fix: store a per-user `timezone_offset` (default IST, +05:30) and route every date/time call through a local-time helper instead of the system clock.

**3. Bedtime overflow**
Early versions let tasks spill past midnight for students with unusual wake/sleep times. Fix: strict 24-hour dropdowns for wake, sleep, and meal times, with the scheduler calculating relative offsets and truncating hard at bedtime.

**4. Clash handling**
When a class, meal, and high-priority assignment all land in the same hour, Orbit doesn't drop anything — it stacks them (`🔴 DSA Homework / 🔴 Chemistry clash`) and falls back to the student's preferred focus window if no empty slot exists.

**5. Overwhelmed mode**
A "Simplify Plan" button clears low-priority tasks, offers to halve study hours, and nudges the student to manually decide what to compromise on if things still feel like too much.

---

## 📈 Lessons learned

1. **Keep business logic deterministic.** AI is great for text, not for calendars — combining Python scheduling with LLM commentary gave the best of both.
2. **Edge cases are the real work.** Sleep offsets, midnight crossings, and timezones needed careful testing.
3. **Clean, modular code saves you later.** A tangled function can crash the whole layout — decoupling early paid off.

---

Orbit is more than a scheduler — it's a supportive friend in a student's pocket. 🪐✨