import streamlit as st
from backend.database import initialize_db, get_connection
from ai.service import generate_day_plan, get_mood_history
from frontend.styling import apply_global_css
import datetime
import re

# Initialize database
initialize_db()

# Page config
st.set_page_config(
    page_title="Orbit",
    page_icon="○",
    layout="wide"
)

# Apply global styling
apply_global_css()

# Helper to parse AI Day Plan and render as a vertical timeline
def render_ai_plan_timeline(plan_text):
    if not plan_text:
        return
    
    # Regex to match time lines (e.g. 09:00 AM — Attend Math Class)
    time_pattern = re.compile(r'^\s*(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?(?:\s*-\s*\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)?)\s*[—\-–:]\s*(.*)', re.IGNORECASE)
    
    html_timeline = '<div class="timeline">'
    matched_any = False
    
    lines = plan_text.split('\n')
    other_blocks = []
    
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
        
        match = time_pattern.match(line_str)
        if match:
            matched_any = True
            time_val = match.group(1).strip()
            activity_val = match.group(2).strip()
            
            # Render timeline item
            html_timeline += f'<div class="timeline-item"><div class="timeline-dot"></div><div class="timeline-content"><div class="timeline-time">{time_val}</div><div class="timeline-activity">{activity_val}</div></div></div>'
        else:
            # Check for header or special section
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
                
    html_timeline += '</div>'
    
    if matched_any:
        st.markdown(html_timeline, unsafe_allow_html=True)
        for block in other_blocks:
            st.markdown(block, unsafe_allow_html=True)
    else:
        # Fallback to standard rendering if no time codes matched
        st.markdown(plan_text)

# ── HEADER ───────────────────────────────────────────────
st.title("Orbit")
st.markdown("<p style='color: #94a3b8; font-size: 1.1rem; margin-top: -15px; margin-bottom: 25px;'>Your personal academic companion</p>", unsafe_allow_html=True)

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
cursor.execute("SELECT mood FROM daily_logs WHERE date = ?", (today,))
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
        st.warning("Already logged today! Come back tomorrow.")
    else:
        cursor.execute(
            "INSERT INTO daily_logs (date, mood, sleep) VALUES (?, ?, ?)",
            (today, mood, sleep)
        )
        conn.commit()
        st.session_state["mood"] = mood
        st.session_state["sleep"] = sleep
        st.session_state["overwhelmed"] = False
        st.session_state["plan"] = None  # Reset plan to force generation
        st.success("Check-in saved! Generating your day plan...")

    conn.close()
    st.rerun()

# Load from session if already logged
if mood_log and "mood" not in st.session_state:
    st.session_state["mood"] = mood_log[0]
    st.session_state["sleep"] = sleep

st.markdown("<hr style='border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

# ── MAIN LAYOUT (2 Columns) ────────────────────────────────
if "mood" in st.session_state:
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("Your Day Plan")
        
        # Lighter plan action
        col_btn_1, col_btn_2 = st.columns([3, 1])
        with col_btn_2:
            if st.button("Simplify Plan"):
                st.session_state["overwhelmed"] = True
                st.session_state["plan"] = None
                st.rerun()
                
        # Generate plan if needed
        if "plan" not in st.session_state or st.session_state.get("plan") is None:
            with st.spinner("Orbit is generating your schedule..."):
                conn = get_connection()
                cursor = conn.cursor()
                
                # Fetch pending tasks
                cursor.execute(
                    "SELECT title, deadline, task_type, is_done FROM tasks WHERE is_done = 0 ORDER BY deadline"
                )
                tasks = cursor.fetchall()
                
                # Fetch goals
                cursor.execute("SELECT title, frequency, target FROM goals")
                goals = cursor.fetchall()
                
                # Fetch classes for today
                today_name = datetime.date.today().strftime("%A")
                cursor.execute(
                    "SELECT subject, day, start_time, end_time FROM timetable WHERE day = ?",
                    (today_name,)
                )
                timetable = cursor.fetchall()
                
                # Fetch subjects to check attendance warning
                cursor.execute("SELECT DISTINCT subject FROM timetable")
                subjects = [row[0] for row in cursor.fetchall()]
                
                attendance_warnings = []
                for subj in subjects:
                    cursor.execute("SELECT COUNT(*) FROM attendance WHERE subject = ?", (subj,))
                    total = cursor.fetchone()[0]
                    cursor.execute("SELECT COUNT(*) FROM attendance WHERE subject = ? AND status = 'Present'", (subj,))
                    attended = cursor.fetchone()[0]
                    if total > 0:
                        percentage = (attended / total) * 100
                        if percentage < 75:
                            attendance_warnings.append((subj, percentage))
                            
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
                    overwhelmed=st.session_state.get("overwhelmed", False)
                )
                
                st.session_state["plan"] = plan
                
        # Render timeline
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
        cursor.execute("SELECT id, title, deadline, task_type FROM tasks WHERE is_done = 0 ORDER BY deadline")
        pending_tasks_list = cursor.fetchall()
        conn.close()
        
        if pending_tasks_list:
            for task_id, title, deadline, task_type in pending_tasks_list:
                clean_type = task_type.replace("🔴 ", "").replace("🔵 ", "").replace("🟡 ", "").replace("🎯 ", "").replace("💙 ", "")
                
                # Render standard checkbox in container
                done = st.checkbox(
                    f"{clean_type} | {title} (due {deadline})",
                    value=False,
                    key=f"home_task_{task_id}"
                )
                if done:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE tasks SET is_done = 1 WHERE id = ?", (task_id,))
                    conn.commit()
                    conn.close()
                    st.session_state["plan"] = None  # Force regenerate
                    st.success("Task completed!")
                    st.rerun()
        else:
            st.info("All tasks completed! Nice job.")
            
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
            submitted = st.form_submit_button("Add Task")
            if submitted:
                if new_title:
                    # Map new priorities to matching DB codes if needed, or keep clean
                    priority_mapping = {
                        "High Priority": "🔴 High Priority",
                        "Medium Priority": "🔵 Medium Priority",
                        "Low Priority": "🟡 Low Priority",
                        "Extracurricular": "🎯 Club / Extracurricular",
                        "Personal": "💙 Personal Goal"
                    }
                    db_priority = priority_mapping.get(new_priority, new_priority)
                    
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO tasks (title, deadline, task_type, is_done) VALUES (?, ?, ?, 0)",
                        (new_title, str(new_deadline), db_priority)
                    )
                    conn.commit()
                    conn.close()
                    st.session_state["plan"] = None  # Force regenerate
                    st.success(f"Added: {new_title}")
                    st.rerun()
                else:
                    st.error("Please enter a task title!")