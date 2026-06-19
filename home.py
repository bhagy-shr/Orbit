import streamlit as st
from backend.database import initialize_db, get_connection
from ai.service import generate_day_plan, get_mood_history, generate_motivation_quote
from frontend.styling import apply_global_css
import datetime
import re

apply_global_css()

# ── LOGGED IN DASHBOARD ───────────────────────────────────

# Load Profile Name
conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT name FROM user_profile LIMIT 1")
user_name = cursor.fetchone()[0]
conn.close()

# ── HEADER ───────────────────────────────────────────────
st.title("Orbit")
st.markdown(f"<p style='color: #94a3b8; font-size: 1.1rem; margin-top: -15px; margin-bottom: 25px;'>Welcome back, {user_name}! Your personal academic companion</p>", unsafe_allow_html=True)

# ── QUICK STATS ──────────────────────────────────────────
conn = get_connection()
cursor = conn.cursor()

# Get streak
cursor.execute("SELECT streak_count FROM streaks ORDER BY date DESC LIMIT 1")
streak_row = cursor.fetchone()
current_streak = streak_row[0] if streak_row else 0

# Get tasks count
cursor.execute("SELECT COUNT(*) FROM tasks WHERE is_done = 0")
pending_tasks = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM tasks WHERE is_done = 1")
done_tasks = cursor.fetchone()[0]
total_tasks = pending_tasks + done_tasks

# Get today's mood log
today = datetime.date.today().strftime("%Y-%m-%d")
cursor.execute("SELECT mood, sleep FROM daily_logs WHERE date = ?", (today,))
mood_log = cursor.fetchone()
conn.close()

today_display = datetime.date.today().strftime("%a, %b %d")
mood_labels = {
    1: "Very Low", 2: "Low",
    3: "Neutral", 4: "Good", 5: "Excellent"
}

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Today", today_display)
with col2:
    st.metric("Streak", f"{current_streak} days")
with col3:
    st.metric("Tasks Completed", f"{done_tasks}/{total_tasks}")
with col4:
    if mood_log:
        st.metric("Mood Today", mood_labels[mood_log[0]])
    else:
        st.metric("Mood Today", "Not logged")

st.markdown("<br>", unsafe_allow_html=True)

# ── DAILY CHECK-IN ───────────────────────────────────────
st.subheader("Daily Check-in")
st.markdown("<p style='color: #94a3b8; font-size: 0.9rem; margin-top: -5px;'>Take 60 seconds to log your status and calibrate your day plan.</p>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    mood = st.slider("How are you feeling today?", 1, 5, 3,
                     help="1 = very low, 5 = excellent")
    st.write(f"Mood: {mood_labels[mood]}")
with col2:
    sleep = st.number_input(
        "How many hours did you sleep?",
        min_value=0.0, max_value=12.0,
        value=7.0, step=0.5
    )

if st.button("Log Check-in & Generate My Day Plan"):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM daily_logs WHERE date = ?", (today,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("UPDATE daily_logs SET mood = ?, sleep = ? WHERE date = ?", (mood, sleep, today))
    else:
        cursor.execute(
            "INSERT INTO daily_logs (date, mood, sleep) VALUES (?, ?, ?)",
            (today, mood, sleep)
        )
    conn.commit()
    conn.close()
    
    st.session_state["mood"] = mood
    st.session_state["sleep"] = sleep
    st.session_state["overwhelmed"] = False
    st.session_state["plan"] = None  # Reset plan to force generation
    st.session_state["motivation_quote"] = None # Force regenerate quote
    st.success("Check-in saved! Calibrating your day plan...")
    st.rerun()

# Load from session if already logged
if mood_log and "mood" not in st.session_state:
    st.session_state["mood"] = mood_log[0]
    st.session_state["sleep"] = mood_log[1]

# ── CRITICAL BUNK ALERTS ──────────────────────────────────
# Load warnings to show bunk restrictions
conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT DISTINCT subject FROM timetable")
db_subjects = [row[0] for row in cursor.fetchall()]

attendance_warnings = []
for subj in db_subjects:
    cursor.execute("SELECT COUNT(*) FROM attendance WHERE subject = ?", (subj,))
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM attendance WHERE subject = ? AND status = 'Present'", (subj,))
    attended = cursor.fetchone()[0]
    
    # Fetch historical attendance offsets
    cursor.execute("SELECT past_attended, past_total FROM attendance_offsets WHERE subject = ?", (subj,))
    offset = cursor.fetchone()
    if offset:
        attended += offset[0]
        total += offset[1]
        
    if total > 0:
        percentage = (attended / total) * 100
        if percentage < 75:
            attendance_warnings.append((subj, percentage))
conn.close()

if attendance_warnings:
    st.markdown("<br>", unsafe_allow_html=True)
    for subj, pct in attendance_warnings:
        st.error(f"⚠️ **Critical Alert: Bunk Warning for {subj}!** Your attendance is currently at **{pct:.1f}%** (below 75%). You must attend this class today to restore your standing.")

st.markdown("<hr style='border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

# Helper to parse AI Day Plan and render as interactive checklist
def render_ai_plan_timeline(plan_text):
    if not plan_text:
        return
    
    time_pattern = re.compile(
        r'^\s*(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?(?:\s*-\s*\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)?)\s*[—\-–:]\s*(.*)', 
        re.IGNORECASE
    )
    
    lines = plan_text.split('\n')
    other_blocks = []
    
    st.markdown("<div class='timeline'>", unsafe_allow_html=True)
    matched_any = False
    
    for i, line in enumerate(lines):
        line_str = line.strip()
        if not line_str:
            continue
        
        match = time_pattern.match(line_str)
        if match:
            matched_any = True
            time_val = match.group(1).strip()
            activity_val = match.group(2).strip()
            
            # Check if this timeline slot is one of the student's scheduled classes
            matched_subject = None
            for subj in db_subjects:
                if subj.lower() in activity_val.lower():
                    matched_subject = subj
                    break
            
            if matched_subject:
                # Class Slot - Render with an Attendance Checkbox
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT status FROM attendance WHERE subject = ? AND date = ?", 
                    (matched_subject, today)
                )
                att_row = cursor.fetchone()
                conn.close()
                
                is_present = (att_row[0] == "Present") if att_row else False
                
                checked = st.checkbox(
                    f"🎓 {time_val} | Class: {activity_val} (Check to mark Present / Uncheck for Absent)",
                    value=is_present,
                    key=f"class_att_{matched_subject}_{i}"
                )
                
                if checked != is_present:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM attendance WHERE subject = ? AND date = ?", (matched_subject, today))
                    cursor.execute(
                        "INSERT INTO attendance (subject, date, status) VALUES (?, ?, ?)",
                        (matched_subject, today, "Present" if checked else "Absent")
                    )
                    conn.commit()
                    conn.close()
                    st.toast(f"Attendance updated for {matched_subject}!")
                    st.rerun()
            else:
                # Generic task/schedule item checkbox
                # Ensure priority circles are present in the text if we see priority keywords
                activity_lower = activity_val.lower()
                if ("high priority" in activity_lower or "high-priority" in activity_lower or "priority: high" in activity_lower) and "🔴" not in activity_val:
                    activity_val = "🔴 " + activity_val
                elif ("medium priority" in activity_lower or "medium-priority" in activity_lower or "priority: medium" in activity_lower) and "🔵" not in activity_val:
                    activity_val = "🔵 " + activity_val
                elif ("low priority" in activity_lower or "low-priority" in activity_lower or "priority: low" in activity_lower) and "🟡" not in activity_val:
                    activity_val = "🟡 " + activity_val

                task_done_key = f"timeline_task_done_{today}_{i}"
                is_done = st.session_state.get(task_done_key, False)
                
                checked = st.checkbox(
                    f"⏳ {time_val} | {activity_val}",
                    value=is_done,
                    key=f"timeline_task_{i}"
                )
                if checked != is_done:
                    st.session_state[task_done_key] = checked
        else:
            # Handle headers or notes block
            upper_line = line_str.upper()
            if upper_line.startswith(("PLAN FOR TODAY", "A GENTLE PLAN", "YOUR LIGHTER PLAN")):
                continue
            elif upper_line.startswith(("NOTE:", "REMEMBER:", "MOTIVATION:", "SUPPORT:", "CHECKING IN:", "I HEAR YOU:", "SKIP TODAY:")):
                parts = line_str.split(':', 1)
                header_name = parts[0].strip()
                content_val = parts[1].strip() if len(parts) > 1 else ""
                
                other_blocks.append(
                    f'<div class="custom-card" style="margin-top: 15px;">'
                    f'<div style="font-weight: 600; color: #60a5fa; margin-bottom: 5px; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">{header_name}</div>'
                    f'<div style="color: #e2e8f0; font-size: 0.9rem;">{content_val}</div>'
                    f'</div>'
                )
            else:
                clean_text = re.sub(r'^[\-\*\s]+', '', line_str)
                other_blocks.append(f'<p style="color: #94a3b8; font-size: 0.9rem; margin: 4px 0;">{clean_text}</p>')
                
    st.markdown("</div>", unsafe_allow_html=True)
    
    if other_blocks:
        st.markdown("<br>", unsafe_allow_html=True)
        for block in other_blocks:
            st.markdown(block, unsafe_allow_html=True)


# ── MAIN LAYOUT (2 Columns) ────────────────────────────────
if "mood" in st.session_state:
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("Your Day Plan")
        
        # Simplify/Tighten/Standard plan buttons
        col_btn_1, col_btn_2, col_btn_3 = st.columns([1, 1, 1])
        with col_btn_1:
            if st.button("Simplify Plan", use_container_width=True):
                st.session_state["overwhelmed"] = True
                st.session_state["motivated"] = False
                st.session_state["plan"] = None
                st.rerun()
        with col_btn_2:
            if st.button("Tighten Schedule", use_container_width=True):
                st.session_state["motivated"] = True
                st.session_state["overwhelmed"] = False
                st.session_state["plan"] = None
                st.rerun()
        with col_btn_3:
            if st.button("Standard Plan", use_container_width=True):
                st.session_state["motivated"] = False
                st.session_state["overwhelmed"] = False
                st.session_state["plan"] = None
                st.rerun()
                
        # Overwhelmed Compromise Dialog
        if st.session_state.get("overwhelmed", False):
            # Fetch active tasks with allocated hours
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, allocated_hours FROM tasks WHERE is_done = 0 AND allocated_hours IS NOT NULL AND allocated_hours > 0")
            tasks_with_hours = cursor.fetchall()
            conn.close()
            
            if tasks_with_hours:
                st.markdown(
                    """
                    <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                        <h4 style="color: #f87171; margin-top: 0; margin-bottom: 5px;">🤕 Compromise Study Hours?</h4>
                        <p style="color: #fca5a5; font-size: 0.9rem; margin-bottom: 10px;">Since you are overwhelmed, would you like to compromise on the allocated study hours for any of your active tasks?</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                for t_id, t_title, t_hours in tasks_with_hours:
                    col_t_lbl, col_t_action = st.columns([3, 1])
                    with col_t_lbl:
                        st.markdown(f"<div style='padding-top: 6px; color: #e2e8f0; font-size: 0.9rem;'>{t_title} (Current: <b>{t_hours}h</b>)</div>", unsafe_allow_html=True)
                    with col_t_action:
                        new_hours = round(t_hours / 2, 1)
                        btn_label = f"Halve to {new_hours}h" if new_hours > 0.1 else "Remove Hours"
                        if st.button(btn_label, key=f"comp_{t_id}", use_container_width=True):
                            conn = get_connection()
                            cursor = conn.cursor()
                            if new_hours <= 0.1:
                                cursor.execute("UPDATE tasks SET allocated_hours = NULL WHERE id = ?", (t_id,))
                            else:
                                cursor.execute("UPDATE tasks SET allocated_hours = ? WHERE id = ?", (new_hours, t_id))
                            conn.commit()
                            conn.close()
                            st.session_state["plan"] = None # Force regenerate
                            st.success(f"Compromised hours for: {t_title}")
                            st.rerun()
                st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

        # Generate Quote first
        if "motivation_quote" not in st.session_state or st.session_state.get("motivation_quote") is None:
            with st.spinner("Orbit is writing your motivational quote..."):
                quote = generate_motivation_quote(st.session_state["mood"], st.session_state["sleep"])
                st.session_state["motivation_quote"] = quote
                
        # Display Quote
        if st.session_state.get("motivation_quote"):
            st.markdown(
                f"""
                <div class="custom-card" style="background: linear-gradient(135deg, rgba(79, 70, 229, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%); border-color: rgba(79, 70, 229, 0.25); margin-bottom: 10px;">
                    <div style="font-size: 0.8rem; font-weight: 600; color: #818cf8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 5px;">Morning Calibrator</div>
                    <div style="font-size: 1.15rem; font-style: italic; color: #ffffff; line-height: 1.5; font-family: 'Outfit';">"{st.session_state['motivation_quote']}"</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Place Chatbot Shortcut Link directly below the quote
            st.page_link(
                "pages/5_Chatbot.py", 
                label="Talk to Orbit AI Friend", 
                icon="💬"
            )
            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
            
        # Generate plan if needed
        if "plan" not in st.session_state or st.session_state.get("plan") is None:
            with st.spinner("Orbit is generating your schedule..."):
                conn = get_connection()
                cursor = conn.cursor()
                
                # Fetch pending tasks
                cursor.execute(
                    "SELECT id, title, deadline, task_type, is_done, allocated_hours, pref_start_time, pref_end_time FROM tasks WHERE is_done = 0 ORDER BY deadline"
                )
                tasks = cursor.fetchall()
                
                # Fetch goals
                cursor.execute("SELECT id, title, frequency, target FROM goals")
                goals = cursor.fetchall()
                
                # Fetch classes for today
                today_name = datetime.date.today().strftime("%A")
                cursor.execute(
                    "SELECT subject, day, start_time, end_time FROM timetable WHERE day = ?",
                    (today_name,)
                )
                timetable = cursor.fetchall()
                conn.close()
                
                # Get mood history
                mood_history = get_mood_history(days=7)
                
                # Generate plan
                plan = generate_day_plan(
                    mood=st.session_state["mood"],
                    sleep=st.session_state["sleep"],
                    tasks=tasks,
                    goals=goals,
                    timetable=timetable,
                    attendance_warnings=attendance_warnings,
                    mood_history=mood_history,
                    overwhelmed=st.session_state.get("overwhelmed", False),
                    motivated=st.session_state.get("motivated", False)
                )
                
                st.session_state["plan"] = plan
                
        # Render timeline checklist
        if "plan" in st.session_state and st.session_state["plan"]:
            render_ai_plan_timeline(st.session_state["plan"])
            
        # Support messages based on mood logs
        mood_history = get_mood_history(days=7)
        low_mood_days = sum(1 for m, s in mood_history if m <= 2)
        
        if low_mood_days >= 5:
            st.error(
                "Orbit has noticed you've been having a tough week. "
                "Your plan today is lighter than usual. "
                "Please consider talking to someone you trust — a friend, family member, or counselor. "
                "You don't have to carry this alone."
            )
        elif low_mood_days >= 3:
            st.warning(
                "You've had a few tough days recently. "
                "Be kind to yourself today — progress is progress, no matter how small."
            )
            
    with col_right:
        st.subheader("Pending Tasks")
        st.markdown("<p style='color: #94a3b8; font-size: 0.9rem; margin-top: -5px; margin-bottom: 15px;'>Check off tasks as you complete them.</p>", unsafe_allow_html=True)
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, deadline, task_type, allocated_hours FROM tasks WHERE is_done = 0 ORDER BY deadline")
        pending_tasks_list = cursor.fetchall()
        conn.close()
        
        if pending_tasks_list:
            for task_id, title, deadline, task_type, alloc_h in pending_tasks_list:
                clean_type = task_type.replace("🔴 ", "").replace("🔵 ", "").replace("🟡 ", "").replace("🎯 ", "").replace("💙 ", "")
                duration_str = f" ({alloc_h}h)" if alloc_h else ""
                
                # Detect priority circle from original DB type
                circle = "⚪"
                if "🔴" in task_type or "High" in task_type:
                    circle = "🔴"
                elif "🔵" in task_type or "Medium" in task_type:
                    circle = "🔵"
                elif "🟡" in task_type or "Low" in task_type:
                    circle = "🟡"
                elif "🎯" in task_type or "Extracurricular" in task_type:
                    circle = "🎯"
                elif "💙" in task_type or "Personal" in task_type:
                    circle = "💙"
                
                # Render standard checkbox in container
                done = st.checkbox(
                    f"{circle} {clean_type} | {title}{duration_str} (due {deadline})",
                    value=False,
                    key=f"home_task_{task_id}"
                )
                if done:
                    conn = get_connection()
                    cursor = conn.cursor()
                    today_str = datetime.date.today().strftime("%Y-%m-%d")
                    cursor.execute("UPDATE tasks SET is_done = 1, completed_date = ? WHERE id = ?", (today_str, task_id))
                    conn.commit()
                    conn.close()
                    st.session_state["plan"] = None  # Force regenerate
                    st.success("Task completed!")
                    st.rerun()
        else:
            st.info("All tasks completed! Nice job.")
            
        st.markdown("<hr style='border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
        
        # Additional Task / Timeline Update Input
        st.write("**Day Plan Adjustments**")
        st.markdown(
            """
            <p style='color: #94a3b8; font-size: 0.85rem; margin-top: -5px; line-height: 1.45;'>
                Request changes or study blocks.<br>
                💡 <b>Note: Always use the 24-hour format (HH:MM-HH:MM)</b> for adjustments (e.g. "Change DSA to 16:00-18:00" or "AI Club meeting from 09:00-11:00" or "ML study in parts: 13:00-14:00 and 16:00-17:00").
            </p>
            """,
            unsafe_allow_html=True
        )
        
        with st.form("additional_tasks_adjustment_form", clear_on_submit=True):
            adjust_input = st.text_area("Adjustment Requests", placeholder="e.g. Add 1 hour break after lunch, reschedule DSA study...")
            submitted_adj = st.form_submit_button("Update Schedule")
            if submitted_adj:
                if adjust_input:
                    # Log adjustments to chatbot insights for scheduling
                    conn = get_connection()
                    cursor = conn.cursor()
                    today_str = datetime.date.today().strftime("%Y-%m-%d")
                    cursor.execute(
                        "INSERT INTO chat_insights (date, insight, category) VALUES (?, ?, ?)",
                        (today_str, f"User adjustment request: {adjust_input}", "schedule_adjustment")
                    )
                    conn.commit()
                    conn.close()
                    st.session_state["plan"] = None  # Force regenerate
                    st.success("Schedule adjustments queued! Regenerating...")
                    st.rerun()
                else:
                    st.error("Please enter adjustment details!")
                    
        st.markdown("<hr style='border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
        
        # Quick add task form
        with st.form("quick_add_task_form", clear_on_submit=True):
            st.write("**Quick Add Task**")
            new_title = st.text_input("Task Title", placeholder="e.g. Read Chapter 4")
            col_date, col_type = st.columns(2)
            with col_date:
                new_deadline = st.date_input("Deadline", value=datetime.date.today())
            with col_type:
                new_priority = st.selectbox(
                    "Priority",
                    ["High Priority", "Medium Priority", "Low Priority", "Extracurricular", "Personal"]
                )
            col_dur, col_pref = st.columns(2)
            with col_dur:
                duration_h = st.number_input("Time to spend (hours)", min_value=0.0, max_value=8.0, value=0.0, step=0.5)
            with col_pref:
                slot_pref = st.text_input(
                    "Preferred slot (e.g. 18:00-20:00 or 13:00-14:00, 16:00-17:00)", 
                    placeholder="HH:MM-HH:MM or multiple slots",
                    help="Always enter slots in 24-hour format"
                )
                
            submitted = st.form_submit_button("Add Task")
            if submitted:
                if new_title:
                    priority_mapping = {
                        "High Priority": "🔴 High Priority",
                        "Medium Priority": "🔵 Medium Priority",
                        "Low Priority": "🟡 Low Priority",
                        "Extracurricular": "🎯 Club / Extracurricular",
                        "Personal": "💙 Personal Goal"
                    }
                    db_priority = priority_mapping.get(new_priority, new_priority)
                    
                    # Parse slot preference (handles single 24h slots or multi-slots)
                    pref_start, pref_end = None, None
                    if slot_pref:
                        slot_pref = slot_pref.strip()
                        if slot_pref.count("-") == 1 and "," not in slot_pref and "and" not in slot_pref:
                            try:
                                start, end = slot_pref.split("-")
                                pref_start = start.strip()
                                pref_end = end.strip()
                            except ValueError:
                                pref_start = slot_pref
                        else:
                            pref_start = slot_pref
                    
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO tasks (title, deadline, task_type, is_done, allocated_hours, pref_start_time, pref_end_time) VALUES (?, ?, ?, 0, ?, ?, ?)",
                        (new_title, str(new_deadline), db_priority, duration_h if duration_h > 0 else None, pref_start, pref_end)
                    )
                    conn.commit()
                    conn.close()
                    st.session_state["plan"] = None  # Force regenerate
                    st.success(f"Added: {new_title}")
                    st.rerun()
                else:
                    st.error("Please enter a task title!")