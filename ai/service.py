import os
import re
import datetime
from groq import Groq

# Try to load Groq API key from KEY.MD if not in environment
if not os.environ.get("GROQ_API_KEY"):
    try:
        with open("KEY.MD", "r") as f:
            content = f.read().strip()
            match = re.search(r'GROQ_API_KEY\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                os.environ["GROQ_API_KEY"] = match.group(1)
    except Exception:
        pass

try:
    client = Groq()
except Exception:
    client = None


def generate_day_plan(mood, sleep, tasks, goals, timetable, 
                      attendance_warnings, mood_history=None, overwhelmed=False):
    
    today = datetime.date.today().strftime("%A, %B %d %Y")
    
    mood_labels = {
        1: "very low — exhausted and struggling",
        2: "low — tired and unmotivated",
        3: "okay — neutral energy",
        4: "good — feeling focused",
        5: "great — high energy and motivated"
    }

    # ── DETECT MOOD PATTERNS ─────────────────────────────
    low_mood_days = 0
    poor_sleep_days = 0
    
    if mood_history:
        for log in mood_history:
            log_mood, log_sleep = log
            if log_mood <= 2:
                low_mood_days += 1
            if log_sleep < 6:
                poor_sleep_days += 1

    struggling = low_mood_days >= 5

    # ── FORMAT CONTEXT ───────────────────────────────────
    tasks_text = ""
    if tasks:
        for task in tasks:
            title, deadline, task_type, is_done = task
            if not is_done:
                tasks_text += f"- {title} ({task_type}) due {deadline}\n"
    else:
        tasks_text = "No pending tasks"

    goals_text = ""
    if goals:
        for goal in goals:
            title, frequency, target = goal
            goals_text += f"- {title} ({frequency}, target: {target})\n"
    else:
        goals_text = "No recurring goals set"

    timetable_text = ""
    if timetable:
        for subject, day, start_time, end_time in timetable:
            timetable_text += f"- {subject}: {start_time} to {end_time}\n"
    else:
        timetable_text = "No classes today"

    warnings_text = ""
    if attendance_warnings:
        for subject, percentage in attendance_warnings:
            warnings_text += f"- {subject}: {percentage:.1f}% (below 75%)\n"
    else:
        warnings_text = "All subjects in good standing"

    # ── MOOD HISTORY SUMMARY ─────────────────────────────
    mood_pattern_text = ""
    if struggling:
        mood_pattern_text = f"""
MOOD PATTERN ALERT:
This student has logged low mood (1-2/5) for {low_mood_days} out of 
the last 7 days and poor sleep (<6 hours) for {poor_sleep_days} days.
This is not just a bad day — this is a pattern that needs gentle attention.
"""
    elif mood_history:
        mood_pattern_text = f"""
RECENT PATTERN:
Low mood days in last 7 days: {low_mood_days}
Poor sleep days in last 7 days: {poor_sleep_days}
"""

    # ── BUILD PROMPT ─────────────────────────────────────
    if struggling:
        # Gentle, care-first prompt
        prompt = f"""
You are Orbit, a warm and caring personal companion for a college student.
Today is {today}.

STUDENT STATUS:
- Mood today: {mood}/5 — {mood_labels[mood]}
- Sleep last night: {sleep} hours
{mood_pattern_text}

TODAY'S CLASSES:
{timetable_text}

PENDING TASKS:
{tasks_text}

ATTENDANCE WARNINGS:
{warnings_text}

This student has been struggling for several days in a row.
Your response should:
- First acknowledge how hard this week has been — warmly, like a friend
- Create a very light, gentle plan with maximum 2-3 priorities only
- Include proper breaks and self-care time
- Explicitly tell them it is okay to not do everything today
- Gently suggest talking to someone they trust — a friend, family member, 
  or their college counselor — not as an alarm, but as a caring nudge
- Never make them feel guilty about low productivity
- Remind them that one hard week does not define their entire semester

Format:
CHECKING IN: [warm acknowledgment of how they've been feeling this week]

A GENTLE PLAN FOR TODAY:
[time] — [activity]
[time] — [activity]
...

REMEMBER: [one gentle reminder that it's okay to not be okay]

SUPPORT: [warm suggestion to reach out to someone they trust]

MOTIVATION: [one short, gentle, encouraging line — nothing toxic positivity]
"""

    elif overwhelmed:
        # Overwhelmed — lighten the plan
        prompt = f"""
You are Orbit, a warm personal companion for a college student.
Today is {today}.

STUDENT STATUS:
- Mood today: {mood}/5 — {mood_labels[mood]}
- Sleep last night: {sleep} hours

TODAY'S CLASSES:
{timetable_text}

PENDING TASKS:
{tasks_text}

ATTENDANCE WARNINGS:
{warnings_text}

The student just told you the original plan felt like too much.
Your response should:
- Acknowledge that feeling overwhelmed is completely valid
- Pick ONLY the single most important task for today
- Build a much lighter plan with longer breaks
- Tell them explicitly what they have permission to skip today
- Be warm and reassuring throughout

Format:
I HEAR YOU: [warm acknowledgment that the plan felt too much]

YOUR LIGHTER PLAN:
[time] — [activity]
[time] — [activity]
...

SKIP TODAY: [what they have permission to let go of today]

MOTIVATION: [one gentle encouraging line]
"""

    else:
        # Normal day plan prompt
        prompt = f"""
You are Orbit, a personal AI companion for a college student.
Today is {today}.

STUDENT STATUS:
- Mood: {mood}/5 — {mood_labels[mood]}
- Sleep last night: {sleep} hours
{mood_pattern_text}

TODAY'S CLASSES:
{timetable_text}

PENDING TASKS AND DEADLINES:
{tasks_text}

RECURRING GOALS:
{goals_text}

ATTENDANCE WARNINGS:
{warnings_text}

Generate a personalized hour-by-hour day plan for this student.

Rules:
- If mood is 1 or 2, keep the plan light and include breaks
- If sleep is less than 6 hours, suggest a short nap and lighter tasks first
- Always protect class time slots — never schedule tasks during classes
- Prioritize tasks that are overdue or due soon
- Fit recurring goals into free slots naturally
- If attendance is below 75% remind student not to miss that class
- End with one short motivational line
- Be warm and friendly — like a supportive friend

Format:
PLAN FOR TODAY:
[time] — [activity]
[time] — [activity]
...

NOTE: [one line explaining why you planned it this way]

MOTIVATION: [one short encouraging line]
"""

    global client
    if client is None:
        try:
            client = Groq()
        except Exception:
            return "Please configure your GROQ_API_KEY environment variable or verify the key inside KEY.MD to generate your day plan."

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content


def get_mood_history(days=7):
    """Fetch last 7 days of mood and sleep logs"""
    from backend.database import get_connection
    import datetime

    conn = get_connection()
    cursor = conn.cursor()

    week_ago = (datetime.date.today() - 
                datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    
    cursor.execute("""
        SELECT mood, sleep FROM daily_logs 
        WHERE date >= ? 
        ORDER BY date DESC
    """, (week_ago,))
    
    history = cursor.fetchall()
    conn.close()
    return history
