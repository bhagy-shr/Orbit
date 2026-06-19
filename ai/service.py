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


def parse_time_to_mins(time_str):
    if not time_str:
        return None
    time_str = time_str.strip()
    try:
        if "AM" in time_str.upper() or "PM" in time_str.upper():
            dt = datetime.datetime.strptime(time_str.upper(), "%I:%M %p")
        else:
            dt = datetime.datetime.strptime(time_str, "%H:%M")
        return dt.hour * 60 + dt.minute
    except ValueError:
        try:
            dt = datetime.datetime.strptime(time_str.upper(), "%H:%M %p")
            return dt.hour * 60 + dt.minute
        except ValueError:
            return None


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
            "Student", "07:00", "23:00", "Evening Focus", "08:00", "13:00", "20:00"
        )

    active_t_norm = active_t
    if active_t_norm == "Evening":
        active_t_norm = "Evening Focus"

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

    # ── BUILD THE DETERMINISTIC TIMETABLE ALGORITHMICALLY ──
    wake_m = parse_time_to_mins(wake_t) or 300
    sleep_m = parse_time_to_mins(sleep_t) or 1380
    bfast_m = parse_time_to_mins(bfast_t) or 480
    lunch_m = parse_time_to_mins(lunch_t) or 780
    dinner_m = parse_time_to_mins(dinner_t) or 1200
    
    if sleep_m < wake_m:
        total_mins = (1440 - wake_m) + sleep_m
    else:
        total_mins = sleep_m - wake_m
        
    def to_relative(m):
        if m is None:
            return None
        r = m - wake_m
        if r < 0:
            r += 1440
        return r

    slot_size = 30
    num_slots = total_mins // slot_size
    slots = [{"start_rel": i * slot_size, "end_rel": (i + 1) * slot_size, "labels": []} for i in range(num_slots)]

    # Helper to check if a relative middle time overlaps a range
    def is_in_range(m, start, end):
        if end > start:
            return start <= m < end
        else:
            return m >= start or m < end

    # 1. Place classes
    if timetable:
        for subject, day, start_time, end_time in timetable:
            s_m = parse_time_to_mins(start_time)
            e_m = parse_time_to_mins(end_time)
            if s_m is not None and e_m is not None:
                for slot in slots:
                    mid = (wake_m + slot["start_rel"] + 15) % 1440
                    if is_in_range(mid, s_m, e_m):
                        slot["labels"].append(f"🎓 Class: {subject}")

    # 2. Place meals (always added)
    def place_fixed_event(start_abs, duration, label):
        for slot in slots:
            mid = (wake_m + slot["start_rel"] + 15) % 1440
            if is_in_range(mid, start_abs, (start_abs + duration) % 1440):
                slot["labels"].append(label)

    place_fixed_event(bfast_m, 30, "🍳 Breakfast")
    place_fixed_event(lunch_m, 45, "🍱 Lunch")
    place_fixed_event(dinner_m, 45, "🍽️ Dinner")

    # 3. Place manual adjustments
    if insights:
        for adj_str, category, duration in insights:
            if category == "schedule_adjustment":
                time_slots = re.findall(r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})', adj_str)
                if time_slots:
                    for start_s, end_s in time_slots:
                        s_m = parse_time_to_mins(start_s)
                        e_m = parse_time_to_mins(end_s)
                        if s_m is not None and e_m is not None:
                            clean_adj = adj_str.replace("User adjustment request:", "").replace("User adjustment request", "").strip()
                            place_fixed_event(s_m, (e_m - s_m) % 1440, f"⚙️ {clean_adj}")

    # 4. Filter and sort tasks
    filtered_tasks = []
    has_high_priority = False
    for task in tasks:
        if len(task) >= 8:
            task_id, title, deadline, task_type, is_done, alloc_h, pref_start, pref_end = task[:8]
        elif len(task) == 5:
            task_id, title, deadline, task_type, is_done = task
            alloc_h, pref_start, pref_end = None, None, None
        else:
            title, deadline, task_type, is_done = task[1], task[2], task[3], task[4]
            alloc_h, pref_start, pref_end = None, None, None

        if overwhelmed and ("low" in str(task_type).lower() or "🟡" in str(task_type)):
            continue  # Drop low priority tasks entirely when overwhelmed

        circle = "⚪"
        if "🔴" in str(task_type) or "High" in str(task_type):
            circle = "🔴"
            has_high_priority = True
        elif "🔵" in str(task_type) or "Medium" in str(task_type):
            circle = "🔵"
        elif "🟡" in str(task_type) or "Low" in str(task_type):
            circle = "🟡"

        filtered_tasks.append({
            "title": title,
            "circle": circle,
            "pref_start": pref_start,
            "pref_end": pref_end,
            "alloc_h": alloc_h or 1.0,
            "scheduled": False
        })

    # Place tasks with preferred slots exactly as they are (even if clash)
    for t in filtered_tasks:
        if t["pref_start"] and t["pref_end"]:
            s_m = parse_time_to_mins(t["pref_start"])
            e_m = parse_time_to_mins(t["pref_end"])
            if s_m is not None and e_m is not None:
                place_fixed_event(s_m, (e_m - s_m) % 1440, f"{t['circle']} {t['title']}")
                t["scheduled"] = True

    # Helper to check if a slot falls inside the user's preferred active window
    def is_slot_in_active(s_rel):
        abs_m = (wake_m + s_rel) % 1440
        if active_t_norm == "Morning Focus":
            if 720 > wake_m:
                return wake_m <= abs_m < 720
            else:
                return abs_m >= wake_m or abs_m < 720
        elif active_t_norm == "Afternoon Focus":
            return 720 <= abs_m < 1020
        elif active_t_norm == "Evening Focus":
            return 1020 <= abs_m < 1260
        else:  # Night Owl Focus: 21:00 to bedtime (sleep_m)
            if sleep_m > 1260:
                return 1260 <= abs_m < sleep_m
            else:
                return abs_m >= 1260 or abs_m < sleep_m

    # Place other tasks based on active window and handle clashes
    unscheduled = [t for t in filtered_tasks if not t["scheduled"]]
    for t in unscheduled:
        duration_mins = int(t["alloc_h"] * 60)
        needed_slots = (duration_mins + 29) // slot_size
        if needed_slots <= 0:
            needed_slots = 1

        # A. Try to find consecutive empty slots inside active window
        scheduled = False
        for i in range(len(slots) - needed_slots + 1):
            if all(not slots[i+j]["labels"] and is_slot_in_active(slots[i+j]["start_rel"]) for j in range(needed_slots)):
                for j in range(needed_slots):
                    slots[i+j]["labels"].append(f"{t['circle']} {t['title']}")
                scheduled = True
                break

        # B. Try to find any empty slots inside active window (non-consecutive)
        if not scheduled:
            empty_active_indices = [idx for idx, slot in enumerate(slots) if not slot["labels"] and is_slot_in_active(slot["start_rel"])]
            if len(empty_active_indices) >= needed_slots:
                for idx in empty_active_indices[:needed_slots]:
                    slots[idx]["labels"].append(f"{t['circle']} {t['title']}")
                scheduled = True

        # C. Try to find consecutive empty slots anywhere in waking window
        if not scheduled:
            for i in range(len(slots) - needed_slots + 1):
                if all(not slots[i+j]["labels"] for j in range(needed_slots)):
                    for j in range(needed_slots):
                        slots[i+j]["labels"].append(f"{t['circle']} {t['title']}")
                    scheduled = True
                    break

        # D. Try to find any empty slots anywhere in waking window
        if not scheduled:
            empty_indices = [idx for idx, slot in enumerate(slots) if not slot["labels"]]
            if len(empty_indices) >= needed_slots:
                for idx in empty_indices[:needed_slots]:
                    slots[idx]["labels"].append(f"{t['circle']} {t['title']}")
                scheduled = True

        # E. Stack inside active window (clash handling - add multiple things to the preferred focus window)
        if not scheduled:
            active_indices = [idx for idx, slot in enumerate(slots) if is_slot_in_active(slot["start_rel"])]
            if active_indices:
                for count in range(needed_slots):
                    idx = active_indices[count % len(active_indices)]
                    slots[idx]["labels"].append(f"{t['circle']} {t['title']}")
                scheduled = True

        # F. Stack inside any waking window slots as absolute fallback
        if not scheduled:
            for count in range(needed_slots):
                idx = count % len(slots)
                slots[idx]["labels"].append(f"{t['circle']} {t['title']}")
            scheduled = True

    # Merge consecutive slots with the exact same combined label string
    merged_events = []
    current_event = None
    for s in slots:
        labels = s["labels"]
        if not labels:
            label_text = "Free Time"
        else:
            # Remove duplicates while preserving order
            seen = set()
            unique_labels = []
            for l in labels:
                if l not in seen:
                    seen.add(l)
                    unique_labels.append(l)
            label_text = " / ".join(unique_labels)

        if current_event and current_event["label"] == label_text:
            current_event["end_rel"] = s["end_rel"]
        else:
            if current_event:
                merged_events.append(current_event)
            current_event = {"start_rel": s["start_rel"], "end_rel": s["end_rel"], "label": label_text}
    if current_event:
        merged_events.append(current_event)

    # Format timetable into standard layout strings
    timetable_lines = []
    timetable_lines.append(f"{wake_t} — 🌅 Morning Routine")
    for ev in merged_events:
        if ev["label"] == "Free Time":
            label_text = "💨 Free Time / Break"
        else:
            label_text = ev["label"]
            
        start_abs = (wake_m + ev["start_rel"]) % 1440
        end_abs = (wake_m + ev["end_rel"]) % 1440
        start_s = f"{start_abs // 60:02d}:{start_abs % 60:02d}"
        end_s = f"{end_abs // 60:02d}:{end_abs % 60:02d}"
        timetable_lines.append(f"{start_s} - {end_s} — {label_text}")
    timetable_lines.append(f"{sleep_t} — 💤 Wind down & Sleep")
    pre_scheduled_timetable = "\n".join(timetable_lines)

    # ── GENERATE CHATBOT FRIENDLY MESSAGES & QUOTE VIA LLM ─
    global client
    if client is None:
        try:
            client = Groq()
        except Exception:
            note_msg = "Take today one step at a time."
            if has_high_priority:
                note_msg = "You have high-priority tasks today. If you are struggling with time, please adjust your timetable manually (using the adjustment box) to decide which tasks you would like to compromise time on."
            if overwhelmed:
                return f"I HEAR YOU: Focus on resting today.\n\nYOUR LIGHTER PLAN:\n{pre_scheduled_timetable}\n\nSKIP TODAY: Low priority tasks\nNOTE: {note_msg}\nMOTIVATION: You got this!"
            else:
                return f"PLAN FOR TODAY:\n{pre_scheduled_timetable}\n\nNOTE: {note_msg}\nMOTIVATION: You got this!"

    prompt = f"""
    You are Orbit, the personal academic AI companion.
    The student's details:
    - Name: {user_name}
    - Mood today: {mood}/5
    - Sleep last night: {sleep} hours
    - Overwhelmed: {overwhelmed}
    - Struggling: {struggling}
    
    Please generate:
    1. A warm daily check-in comment (1-2 sentences) acknowledging their mood/sleep.
    2. A recommendation of what they can skip or let go of today to rest (1 sentence), or "None" if they are fine.
    3. A short encouragement note (1 sentence). If they have High Priority tasks today, you MUST include this exact warning message: "You have high-priority tasks today. If you are struggling with time, please adjust your timetable manually (using the adjustment box) to decide which tasks you would like to compromise time on."
    4. A short motivational quote (1 sentence).
    
    Format your response exactly as:
    CHECKING IN: [text]
    SKIP TODAY: [text]
    NOTE: [text]
    MOTIVATION: [text]
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            max_tokens=400,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        llm_text = response.choices[0].message.content
    except Exception:
        llm_text = ""

    # Parse response elements
    checking_in = "Hope you're having a good start to your day!"
    skip_today = "None"
    note = "Take things one step at a time."
    motivation = "You've got this! Let's make today count. ✨"

    for line in llm_text.split("\n"):
        if line.upper().startswith("CHECKING IN:"):
            checking_in = line.split(":", 1)[1].strip()
        elif line.upper().startswith("SKIP TODAY:"):
            skip_today = line.split(":", 1)[1].strip()
        elif line.upper().startswith("NOTE:"):
            note = line.split(":", 1)[1].strip()
        elif line.upper().startswith("MOTIVATION:"):
            motivation = line.split(":", 1)[1].strip()

    # Enforce compromise note programmatically
    if has_high_priority:
        note = "You have high-priority tasks today. If you are struggling with time, please adjust your timetable manually (using the adjustment box) to decide which tasks you would like to compromise time on."

    # Assemble plan output based on status
    if struggling:
        combined_plan = f"""CHECKING IN: {checking_in}

A GENTLE PLAN FOR TODAY:
{pre_scheduled_timetable}

REMEMBER: {note}
SUPPORT: Talk to someone you trust if you feel down.
MOTIVATION: {motivation}"""
    elif overwhelmed:
        combined_plan = f"""I HEAR YOU: {checking_in}

YOUR LIGHTER PLAN:
{pre_scheduled_timetable}

SKIP TODAY: {skip_today}
NOTE: {note}
MOTIVATION: {motivation}"""
    else:
        combined_plan = f"""PLAN FOR TODAY:
{pre_scheduled_timetable}

NOTE: {note}
MOTIVATION: {motivation}"""

    return combined_plan


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
