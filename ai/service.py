import os
import re
import datetime
from groq import Groq
from backend.database import get_connection, get_local_today

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


def to_24h(time_str):
    if not time_str:
        return time_str
    t_clean = time_str.strip().upper()
    if "AM" in t_clean or "PM" in t_clean:
        try:
            dt = datetime.datetime.strptime(t_clean, "%I:%M %p")
            return dt.strftime("%H:%M")
        except ValueError:
            try:
                dt = datetime.datetime.strptime(t_clean, "%H:%M %p")
                return dt.strftime("%H:%M")
            except ValueError:
                pass
    return t_clean


def generate_motivation_quote(mood, sleep):
    """Generates a highly personalized motivation quote based on mood and energy (sleep)"""
    global client
    if client is None:
        try:
            client = Groq()
        except Exception:
            return "Believe in yourself and take it one step at a time! 💫"

    mood_labels = {
        1: "very low", 2: "low",
        3: "okay", 4: "good", 5: "excellent"
    }
    mood_str = mood_labels.get(mood, "neutral")

    prompt = f"""
    The student is feeling {mood_str} (mood score: {mood}/5) and got {sleep} hours of sleep last night.
    Generate a single, short, highly inspiring and supportive motivational quote (1-2 sentences max) to help them kickstart their day.
    Be warm, friendly, and supportive. Avoid generic clichés, toxic positivity, or cheesy slogans. Focus on gentle encouragement.
    Do not include any quotation marks, introduction, or headers in your response. Just output the raw quote text.
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            max_tokens=150,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip().replace('"', '')
    except Exception:
        return "You are doing great! Let's take today one step at a time. ✨"


def generate_day_plan(mood, sleep, tasks, goals, timetable, 
                      attendance_warnings, mood_history=None, overwhelmed=False, motivated=False):
    
    today = get_local_today().strftime("%A, %B %d %Y")
    today_date_str = get_local_today().strftime("%Y-%m-%d")
    
    mood_labels = {
        1: "very low — exhausted and struggling",
        2: "low — tired and unmotivated",
        3: "okay — neutral energy",
        4: "good — feeling focused",
        5: "great — high energy and motivated"
    }

    # ── FETCH USER PROFILE & SETTINGS ────────────────────
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, wake_time, sleep_time, active_time, breakfast_time, lunch_time, dinner_time 
        FROM user_profile LIMIT 1
    """)
    profile_row = cursor.fetchone()
    
    # ── FETCH CHATBOT INSIGHTS (HABITS/DISTRACTIONS) ──────
    cursor.execute("""
        SELECT insight, category, duration_hours 
        FROM chat_insights 
        WHERE date = ? OR date = ?
        ORDER BY id DESC LIMIT 5
    """, (today_date_str, 
          (get_local_today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")))
    insights = cursor.fetchall()
    conn.close()

    if profile_row:
        user_name, wake_t, sleep_t, active_t, bfast_t, lunch_t, dinner_t = profile_row
        wake_t = to_24h(wake_t)
        sleep_t = to_24h(sleep_t)
        bfast_t = to_24h(bfast_t)
        lunch_t = to_24h(lunch_t)
        dinner_t = to_24h(dinner_t)
    else:
        user_name, wake_t, sleep_t, active_t, bfast_t, lunch_t, dinner_t = (
            "Student", "07:00", "23:00", "Evening", "08:00", "13:00", "20:00"
        )

    # ── DETECT MOOD PATTERNS & SLEEP DEBT ─────────────────
    low_mood_days = 0
    poor_sleep_days = 0
    sleep_debt = 0.0
    recent_sleep_log = []
    
    if mood_history:
        for idx, log in enumerate(mood_history):
            log_mood, log_sleep = log
            recent_sleep_log.append(f"Day -{idx+1}: {log_sleep} hours")
            if log_mood <= 2:
                low_mood_days += 1
            if log_sleep < 6:
                poor_sleep_days += 1
            if log_sleep < 7.0:
                sleep_debt += (7.0 - log_sleep)
                
    recent_sleep_text = ", ".join(recent_sleep_log) if recent_sleep_log else "No recent sleep logged."
    struggling = low_mood_days >= 5

    # ── FORMAT CONTEXT FOR PROMPT ────────────────────────
    tasks_text = ""
    if tasks:
        for task in tasks:
            # Handle task list elements safely depending on tuple length
            if len(task) >= 8:
                task_id, title, deadline, task_type, is_done, allocated_hours, pref_start, pref_end = task[:8]
            elif len(task) == 5:
                task_id, title, deadline, task_type, is_done = task
                allocated_hours, pref_start, pref_end = None, None, None
            else:
                title, deadline, task_type, is_done = task[1], task[2], task[3], task[4]
                allocated_hours, pref_start, pref_end = None, None, None

            if not is_done:
                details = []
                if allocated_hours:
                    details.append(f"duration: {allocated_hours} hours")
                if pref_start and pref_end:
                    details.append(f"preferred slot: {pref_start} to {pref_end}")
                elif pref_start:
                    details.append(f"preferred slot: {pref_start}")
                
                details_str = f" ({', '.join(details)} )" if details else ""
                tasks_text += f"- {title} [{task_type}]{details_str} due {deadline}\n"
    else:
        tasks_text = "No pending tasks"

    goals_text = ""
    if goals:
        for goal in goals:
            title, frequency, target = goal[1], goal[2], goal[3]
            goals_text += f"- {title} ({frequency}, target: {target})\n"
    else:
        goals_text = "No recurring goals set"

    timetable_text = ""
    if timetable:
        for subject, day, start_time, end_time in timetable:
            timetable_text += f"- {subject} Class: {start_time} to {end_time}\n"
    else:
        timetable_text = "No classes today"

    warnings_text = ""
    if attendance_warnings:
        for subject, percentage in attendance_warnings:
            warnings_text += f"- {subject}: {percentage:.1f}% (below 75%)\n"
    else:
        warnings_text = "All subjects in good standing"

    insights_text = ""
    if insights:
        for insight_str, category, duration in insights:
            if category == "schedule_adjustment":
                insights_text += f"- Manual User Schedule Adjustment: {insight_str}\n"
            else:
                dur_str = f" ({duration}h)" if duration else ""
                insights_text += f"- Focus Warning: {insight_str}{dur_str} [Category: {category}]\n"
    else:
        insights_text = "No recent behavioral alerts"

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

    # ── BUILD SYSTEM INSTRUCTIONS & SCHEDULING RULES ─────
    instructions = f"""
You are Orbit, a personal AI academic companion for a college student named {user_name}.
Today is {today}.

STUDENT PREFERENCES & WANTS:
- Waking Time: {wake_t}
- Bedtime: {sleep_t}
- Most Active Study Window: {active_t}
- Meal Times: Breakfast at {bfast_t}, Lunch at {lunch_t}, Dinner at {dinner_t}

STUDENT STATUS:
- Mood today: {mood}/5 — {mood_labels[mood]}
- Sleep last night: {sleep} hours
- Recent Sleep History (last 7 days): {recent_sleep_text}
- Cumulative Sleep Debt: {sleep_debt:.1f} hours
{mood_pattern_text}

TODAY'S TIMETABLE CLASSES:
{timetable_text}

PENDING TASKS & DEDICATED SLOTS:
{tasks_text}

RECURRING GOALS:
{goals_text}

ATTENDANCE CRITICALITY:
{warnings_text}

BEHAVIORAL REMINDERS (FROM CHAT BOT):
{insights_text}

CRITICAL SCHEDULING RULES:
1. **STRICT WAKE-UP & BEDTIME BOUNDARIES**: The generated hourly schedule MUST start exactly at the wake-up time ({wake_t}) and end exactly at the bedtime ({sleep_t}). Under NO circumstances should any slot, activity, class, or task be scheduled before {wake_t} or after {sleep_t} (for example, if wake-up is 05:00 and bedtime is 21:00, there must be absolutely no slots earlier than 05:00 or later than 21:00 in your output plan). The very first item must be at {wake_t} and the very last item must be at {sleep_t}. **24-HOUR FORMAT**: You MUST format all scheduled entries using the 24-hour method (HH:MM - HH:MM) in your generated plan. Never use 12-hour AM/PM formatting in the hourly slots (e.g. output `16:00 - 17:00` instead of `04:00 PM - 05:00 PM`).
2. Always respect class timetables ({timetable_text}) — never schedule tasks or study sessions during class hours. CRITICAL: Do NOT split, break up, or modify the start and end times of scheduled classes or meetings (e.g. if a class/meeting is scheduled from 09:00 to 11:00, you must list it exactly as "09:00 - 11:00 — Class: [Name]". Do NOT break it into chunks like "09:30 - 10:00"). Preserve class and meeting timings exactly.
3. Protect breakfast, lunch, and dinner times based on their meal schedule.
4. **TASK SLOT PRIORITIZATION**: If a task specifies a "preferred slot" (e.g. `18:00-20:00` or split slots like `13:00-14:00 and 16:00-17:00`), you MUST schedule it in that exact slot. This is a top scheduling priority. Never place it in a different time slot. If the slot has multiple parts, schedule the task split into those specific blocks. Check your start/end time math carefully to ensure the duration is fully met.
   - If there is a scheduling conflict:
     * Resolve by Task Priority: High Priority > Medium Priority > Low Priority.
     * If both conflicting tasks are High Priority, schedule them on a first-come, first-served (FCFS) basis (schedule the one listed first in the prompt list first, and push the second one to the next available free study slot).
5. **CRITICAL DEADLINE SAFEGUARD**: If a task's deadline is TODAY ({today_date_str}), you MUST schedule it on today's plan under all circumstances (even if the student is overwhelmed or wants a light day). Never omit a task due today.
6. **DAILY TASK SCALING (NO DROPPING)**: If a task represents a daily quantity target (e.g. '5 practice questions', '10 exercise problems') and the student is overwhelmed (overwhelmed = True), do NOT drop it completely. Instead, scale the quantity down (e.g., reduce it to '2 practice questions' or '1 practice question') to help them keep their daily habit alive.
7. If the student has behavioral reminders (e.g. scrolling reels warnings), explicitly insert custom warning tasks/reminders in their schedule (e.g. "20:00 — NO Instagram reels! Work on study instead").
8. If attendance is below 75% for a subject class today, mark it clearly in their class schedule event as a "Critical - Cannot Bunk!" reminder.
9. **VISUAL PRIORITY CIRCLES**: You MUST depict every task in the day plan schedule with its priority circle: 🔴 for High Priority, 🔵 for Medium Priority, and 🟡 for Low Priority (e.g., '10:00 — 🔴 [High Priority Task Name]' or '15:30 — 🟡 [Low Priority Task Name]'). Make sure the appropriate circle prefix is placed before the task name.
10. **MANUAL ADJUSTMENTS OVERRIDE**: If a manual user adjustment request is provided (e.g., '- Manual User Schedule Adjustment: User adjustment request: my [Event Name] from 09:00-11:00' or 'User adjustment request: add [Task/Subject] study block at 16:00-18:00' or in parts like 'User adjustment request: [Task/Subject] study 13:00-14:00 and 16:00-17:00'), you MUST prioritize and implement this change exactly as requested in today's day plan schedule in 24-hour format. This is a direct command from the user: you must override other scheduling constraints (including class timetables or overwhelmed/motivated modes) to schedule this specific block at the exact time and duration specified. Shift other blocks (study times, breaks, meals) around it as necessary to accommodate it.
11. **ALLOCATED HOURS REQUIREMENT**: If a task has allocated hours (e.g. 2 hours), you MUST schedule the exact number of hours entered for that task. The scheduled block start and end times MUST span the exact duration (e.g. a 2-hour task must be scheduled as a single 2-hour block like '18:00 - 20:00', or split into parts like '13:00-14:00 and 16:00-17:00' that sum to exactly 2 hours). Check your start/end time math carefully to ensure the duration is fully met.
12. **SLEEP TARGET & DEBT ADJUSTMENT**:
    - If the student has logged a pattern of sleep deprivation (recent days of 4h, 6h, etc., resulting in a high Cumulative Sleep Debt) AND they have a relatively light task workload today, you MUST gently remind them in the 'NOTE' or 'MOTIVATION' section to sleep early, and schedule their bedtime 1-2 hours earlier in the generated timetable (e.g., schedule '21:00 — Wind down & Sleep early to recover from sleep debt' if normal bedtime is 22:00 or 23:00).
    - If the student explicitly asks to adjust the timetable to maintain their 7 hours of sleep (e.g. in the Manual User Schedule Adjustment), you MUST adjust the wake-up time or bedtime in the generated schedule to guarantee at least 7 hours of sleep, even if you have to compress study sessions.
13. **STRICT TASK INTEGRITY (ZERO HALLUCINATIONS)**: You MUST ONLY schedule tasks, classes, and goals that are explicitly listed in the prompt context. Do NOT invent, assume, or add any tasks (such as 'Study DSA midterm', 'Read novel', 'Chemistry test', or any other task names or mock examples) that are not present in the student's task list, timetable, or adjustment requests. If a task is not in the data, do not schedule study blocks for it under any circumstance. If the user's task list is empty (reads 'No pending tasks'), do not schedule any task study blocks at all.
"""

    if struggling:
        prompt = f"""
{instructions}
Create a very light, gentle schedule with maximum 2-3 priorities. Focus heavily on self-care, simple breaks, and warm, friendly support. Encourage them gently to talk to someone they trust if this low mood pattern persists.

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
        prompt = f"""
{instructions}
The student just indicated they feel overwhelmed. Simplify the schedule. Pick only the single most important task for today (ensuring it's the highest priority with the tightest deadline) and make the rest of the schedule extremely light, with long breaks. Keep high priority tasks due today, and scale down daily quantitative targets (e.g. "5 CP questions" becomes "2 CP questions") instead of removing them.
**CRITICAL**: If the user has manually requested a schedule adjustment (like increasing study time for a specific subject or task), you MUST honor this request and schedule the increased study block for that subject/task today, overriding the simplified/light guidelines for that specific item.

Format:
I HEAR YOU: [warm acknowledgment that the plan felt too much]

YOUR LIGHTER PLAN:
[time] — [activity]
[time] — [activity]
...

SKIP TODAY: [what they have permission to let go of today to rest]
MOTIVATION: [one gentle encouraging line]
"""
    elif motivated:
        prompt = f"""
{instructions}
The student is highly motivated today! Generate a high-intensity study schedule. Squeeze in more tasks, reduce leisure/break times (make breaks shorter, e.g., 10 mins), group focus sessions together, and maximize their active study window ({active_t}). Call these study blocks 'DEEP FOCUS WORKTIME' in the timeline.

Format:
PLAN FOR TODAY:
[time] — [activity]
[time] — [activity]
...

NOTE: [one line explaining why you planned it this way]
MOTIVATION: [one short encouraging line]
"""
    else:
        prompt = f"""
{instructions}
Generate a structured, balanced daily plan for today. Maximize focus during their active study window ({active_t}). 

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

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error contacting Groq API: {str(e)}"


def get_mood_history(days=7):
    """Fetch last 7 days of mood and sleep logs"""
    from backend.database import get_connection, get_local_today
    import datetime

    conn = get_connection()
    cursor = conn.cursor()

    week_ago = (get_local_today() - 
                datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    
    cursor.execute("""
        SELECT mood, sleep FROM daily_logs 
        WHERE date >= ? 
        ORDER BY date DESC
    """, (week_ago,))
    
    history = cursor.fetchall()
    conn.close()
    return history
