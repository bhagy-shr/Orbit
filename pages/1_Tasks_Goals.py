import streamlit as st
from backend.database import get_connection
import datetime
from frontend.styling import apply_global_css

# Page setup
# set_page_config configured in router

# Apply global styling
apply_global_css()

st.title("Quests & Habits")
st.markdown("<p style='color: #94a3b8; font-size: 1.1rem; margin-top: -15px; margin-bottom: 25px;'>Track your academic deadlines, assign duration preferences, and manage recurring habits.</p>", unsafe_allow_html=True)

# 2-Column Layout
col_tasks, col_goals = st.columns([1, 1])

# ── COLUMN 1: TASKS & DEADLINES ───────────────────────────
with col_tasks:
    st.subheader("Academic Quests")
    st.markdown("<p style='color: #94a3b8; font-size: 0.9rem; margin-top: -5px; margin-bottom: 15px;'>Manage tasks, allocate study durations, and specify preferred slots.</p>", unsafe_allow_html=True)
    
    # Edit Task Panel
    edit_id = st.session_state.get("edit_task_id")
    if edit_id:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT title, deadline, task_type, allocated_hours, pref_start_time, pref_end_time FROM tasks WHERE id = ?", (edit_id,))
        task_to_edit = cursor.fetchone()
        conn.close()
        
        if task_to_edit:
            t_title, t_deadline, t_type, t_alloc, t_start, t_end = task_to_edit
            
            # Prefill values
            try:
                deadline_val = datetime.date.fromisoformat(t_deadline)
            except ValueError:
                deadline_val = datetime.date.today()
                
            priority_options = ["High Priority", "Medium Priority", "Low Priority", "Club / Extracurricular", "Personal Goal"]
            mapped_type = "Medium Priority"
            if "High" in t_type:
                mapped_type = "High Priority"
            elif "Medium" in t_type:
                mapped_type = "Medium Priority"
            elif "Low" in t_type:
                mapped_type = "Low Priority"
            elif "Club" in t_type or "Extracurricular" in t_type:
                mapped_type = "Club / Extracurricular"
            elif "Personal" in t_type:
                mapped_type = "Personal Goal"
                
            duration_val = float(t_alloc) if t_alloc else 1.0
            slot_val = f"{t_start}-{t_end}" if (t_start and t_end) else ""
            
            st.markdown(
                f"""
                <div style="background: rgba(59, 130, 246, 0.05); border: 1px solid rgba(59, 130, 246, 0.2); padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <h4 style="color: #60a5fa; margin-top: 0; margin-bottom: 10px;">📝 Edit Quest: "{t_title}"</h4>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            with st.form("edit_task_form_details"):
                edit_title = st.text_input("Task Title", value=t_title)
                col_e_date, col_e_priority = st.columns(2)
                with col_e_date:
                    edit_deadline = st.date_input("Deadline", value=deadline_val)
                with col_e_priority:
                    edit_priority = st.selectbox("Priority Category", priority_options, index=priority_options.index(mapped_type))
                    
                col_e_dur, col_e_slot = st.columns(2)
                with col_e_dur:
                    edit_duration = st.number_input("Time allocation (hours)", min_value=0.0, max_value=8.0, value=duration_val, step=0.5)
                with col_e_slot:
                    edit_slot = st.text_input(
                        "Preferred slot (e.g. 18:00-20:00 or 13:00-14:00, 16:00-17:00)", 
                        value=slot_val,
                        help="Always enter slots in 24-hour format (HH:MM-HH:MM)"
                    )
                    
                col_sub1, col_sub2 = st.columns([1, 1])
                with col_sub1:
                    save_changes = st.form_submit_button("Save Changes")
                with col_sub2:
                    cancel_edit = st.form_submit_button("Cancel Edit")
                    
                if save_changes:
                    priority_mapping = {
                        "High Priority": "🔴 High Priority",
                        "Medium Priority": "🔵 Medium Priority",
                        "Low Priority": "🟡 Low Priority",
                        "Club / Extracurricular": "🎯 Club / Extracurricular",
                        "Personal Goal": "💙 Personal Goal"
                    }
                    db_priority = priority_mapping.get(edit_priority, edit_priority)
                    
                    pref_start, pref_end = None, None
                    if edit_slot:
                        edit_slot = edit_slot.strip()
                        if edit_slot.count("-") == 1 and "," not in edit_slot and "and" not in edit_slot:
                            try:
                                start, end = edit_slot.split("-")
                                pref_start = start.strip()
                                pref_end = end.strip()
                            except ValueError:
                                pref_start = edit_slot
                        else:
                            pref_start = edit_slot
                            
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE tasks 
                        SET title = ?, deadline = ?, task_type = ?, allocated_hours = ?, pref_start_time = ?, pref_end_time = ?
                        WHERE id = ?
                    """, (edit_title.strip(), str(edit_deadline), db_priority, edit_duration if edit_duration > 0 else None, pref_start, pref_end, edit_id))
                    conn.commit()
                    conn.close()
                    
                    st.session_state["edit_task_id"] = None
                    st.session_state["plan"] = None  # Force regenerate
                    st.success("Changes saved successfully!")
                    st.rerun()
                    
                if cancel_edit:
                    st.session_state["edit_task_id"] = None
                    st.rerun()
                    
    # Add Task Form
    with st.expander("➕ Add New Task", expanded=False):
        with st.form("add_task_full_form", clear_on_submit=True):
            new_title = st.text_input("Task Title", placeholder="e.g. Complete Chemistry assignment")
            col_date, col_priority = st.columns(2)
            with col_date:
                new_deadline = st.date_input("Deadline", value=datetime.date.today())
            with col_priority:
                new_priority = st.selectbox(
                    "Priority Category",
                    ["High Priority", "Medium Priority", "Low Priority", "Club / Extracurricular", "Personal Goal"]
                )
            
            col_dur, col_slot = st.columns(2)
            with col_dur:
                duration_h = st.number_input(
                    "Time allocation (hours)", 
                    min_value=0.0, max_value=8.0, 
                    value=1.0, step=0.5,
                    help="How many hours do you plan to study for this task?"
                )
            with col_slot:
                slot_pref = st.text_input(
                    "Preferred slot (e.g. 18:00-20:00 or 13:00-14:00, 16:00-17:00)", 
                    placeholder="HH:MM-HH:MM or multiple slots",
                    help="Always enter slots in 24-hour format (HH:MM-HH:MM)"
                )
                
            submitted_task = st.form_submit_button("Create Task")
            if submitted_task:
                if new_title:
                    priority_mapping = {
                        "High Priority": "🔴 High Priority",
                        "Medium Priority": "🔵 Medium Priority",
                        "Low Priority": "🟡 Low Priority",
                        "Extracurricular": "🎯 Club / Extracurricular",
                        "Personal": "💙 Personal Goal"
                    }
                    db_priority = priority_mapping.get(new_priority, new_priority)
                    
                    # Parse slot (handles single 24h slots or multi-slots)
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
                    cursor.execute("""
                        INSERT INTO tasks (title, deadline, task_type, is_done, allocated_hours, pref_start_time, pref_end_time)
                        VALUES (?, ?, ?, 0, ?, ?, ?)
                    """, (new_title.strip(), str(new_deadline), db_priority, duration_h if duration_h > 0 else None, pref_start, pref_end))
                    conn.commit()
                    conn.close()
                    st.success(f"Added quest: {new_title}")
                    st.rerun()
                else:
                    st.error("Please enter a task title!")
                    
    # Render Tasks List
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, deadline, task_type, allocated_hours, pref_start_time, pref_end_time 
        FROM tasks 
        WHERE is_done = 0 
        ORDER BY deadline ASC, id ASC
    """)
    active_tasks = cursor.fetchall()
    
    cursor.execute("""
        SELECT id, title, deadline, task_type, completed_date 
        FROM tasks 
        WHERE is_done = 1 
        ORDER BY completed_date DESC LIMIT 10
    """)
    completed_tasks = cursor.fetchall()
    conn.close()
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.write("**Pending Quests**")
    if active_tasks:
        for task_id, title, deadline, task_type, alloc_h, start_s, end_s in active_tasks:
            clean_type = task_type.replace("🔴 ", "").replace("🔵 ", "").replace("🟡 ", "").replace("🎯 ", "").replace("💙 ", "")
            details_list = []
            if alloc_h:
                details_list.append(f"{alloc_h}h")
            if start_s and end_s:
                details_list.append(f"{start_s}-{end_s}")
            
            details_str = f" [{', '.join(details_list)}]" if details_list else ""
            
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
            
            col_check, col_edit, col_del = st.columns([6, 1, 1])
            with col_check:
                done = st.checkbox(
                    f"{circle} {clean_type} | {title}{details_str} (due {deadline})",
                    value=False,
                    key=f"task_done_chk_{task_id}"
                )
                if done:
                    conn = get_connection()
                    cursor = conn.cursor()
                    today_str = datetime.date.today().strftime("%Y-%m-%d")
                    cursor.execute("UPDATE tasks SET is_done = 1, completed_date = ? WHERE id = ?", (today_str, task_id))
                    conn.commit()
                    conn.close()
                    st.success("Task completed!")
                    st.rerun()
            with col_edit:
                if st.button("📝", key=f"edit_task_btn_{task_id}", help="Edit Task"):
                    st.session_state["edit_task_id"] = task_id
                    st.rerun()
            with col_del:
                if st.button("🗑️", key=f"del_task_btn_{task_id}", help="Delete Task"):
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                    conn.commit()
                    conn.close()
                    st.warning("Task deleted.")
                    st.rerun()
    else:
        st.info("No active quests! Relax or add new ones.")
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.write("**Recently Completed Quests**")
    if completed_tasks:
        for task_id, title, deadline, task_type, completed_d in completed_tasks:
            clean_type = task_type.replace("🔴 ", "").replace("🔵 ", "").replace("🟡 ", "").replace("🎯 ", "").replace("💙 ", "")
            st.markdown(
                f"""
                <div style="font-size: 0.9rem; color: #64748b; text-decoration: line-through; padding: 4px 0;">
                    ✓ {clean_type} | {title} (completed: {completed_d})
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.write("<p style='color: #64748b; font-size: 0.85rem; font-style: italic;'>No completed tasks logged</p>", unsafe_allow_html=True)

# ── COLUMN 2: RECURRING GOALS & HABITS ─────────────────────
with col_goals:
    st.subheader("Daily & Weekly Habits")
    st.markdown("<p style='color: #94a3b8; font-size: 0.9rem; margin-top: -5px; margin-bottom: 15px;'>Establish habits and lock in daily consistency streaks.</p>", unsafe_allow_html=True)
    
    # Add Goal Form
    with st.expander("➕ Add New Habit/Goal", expanded=False):
        with st.form("add_goal_full_form", clear_on_submit=True):
            goal_title = st.text_input("Habit Title", placeholder="e.g. Meditate for 10 minutes")
            col_freq, col_target = st.columns(2)
            with col_freq:
                frequency = st.selectbox("Frequency", ["Daily", "Weekly"])
            with col_target:
                target = st.text_input("Target", placeholder="e.g. 10 mins, 5 pages")
                
            submitted_goal = st.form_submit_button("Create Habit")
            if submitted_goal:
                if goal_title:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO goals (title, frequency, target)
                        VALUES (?, ?, ?)
                    """, (goal_title.strip(), frequency, target.strip()))
                    conn.commit()
                    conn.close()
                    st.success(f"Added habit: {goal_title}")
                    st.rerun()
                else:
                    st.error("Please enter a habit title!")
                    
    # Render Goals list
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, frequency, target FROM goals ORDER BY id ASC")
    active_goals = cursor.fetchall()
    
    # Fetch current streak count
    cursor.execute("SELECT streak_count, date FROM streaks ORDER BY date DESC LIMIT 1")
    streak_row = cursor.fetchone()
    current_streak = streak_row[0] if streak_row else 0
    conn.close()
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.write("**My Active Habits**")
    if active_goals:
        for goal_id, title, freq, trg in active_goals:
            col_goal_text, col_goal_del = st.columns([7, 1])
            with col_goal_text:
                st.markdown(
                    f"""
                    <div class="custom-card" style="padding: 12px; margin-bottom: 8px;">
                        <div style="font-weight: 500; font-size: 0.95rem; color: #ffffff;">{title}</div>
                        <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 3px;">{freq} — Target: {trg}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col_goal_del:
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_goal_btn_{goal_id}", help="Delete Habit"):
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
                    conn.commit()
                    conn.close()
                    st.warning("Habit deleted.")
                    st.rerun()
    else:
        st.info("No active habits set. Lock in some daily routines!")
        
    st.markdown("<hr style='border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
    
    # Streaks Widget
    st.subheader("Streak Tracker")
    st.markdown(
        f"""
        <div class="custom-card" style="background: linear-gradient(135deg, rgba(239, 68, 68, 0.05) 0%, rgba(245, 158, 11, 0.05) 100%); border-color: rgba(245, 158, 11, 0.2); text-align: center; padding: 25px;">
            <div style="font-size: 3rem; margin-bottom: 5px;">🔥</div>
            <div style="font-size: 2.2rem; font-weight: 700; color: #f59e0b; font-family: 'Outfit';">{current_streak} Days</div>
            <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 5px; text-transform: uppercase; letter-spacing: 0.05em;">Current Consistency Streak</div>
        </div>
        """,
        unsafe_allow_html=True
    )
