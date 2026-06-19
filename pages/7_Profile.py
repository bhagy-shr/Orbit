import streamlit as st
from backend.database import get_connection
import datetime
from frontend.styling import apply_global_css

# Page setup
# set_page_config configured in router

# Apply global styling
apply_global_css()

st.title("My Profile & Configuration")
st.markdown("<p style='color: #94a3b8; font-size: 1.1rem; margin-top: -15px; margin-bottom: 25px;'>Update your preferences, time windows, and attendance offsets.</p>", unsafe_allow_html=True)

# Fetch current profile
conn = get_connection()
cursor = conn.cursor()
cursor.execute("""
    SELECT name, wake_time, sleep_time, active_time, breakfast_time, lunch_time, dinner_time 
    FROM user_profile LIMIT 1
""")
profile_row = cursor.fetchone()

# Fetch current semester dates
cursor.execute("SELECT start_date, end_date FROM semester LIMIT 1")
sem_row = cursor.fetchone()

# Fetch unique subjects from timetable
cursor.execute("SELECT DISTINCT subject FROM timetable")
subjects = [r[0] for r in cursor.fetchall()]
conn.close()

if not profile_row:
    st.warning("Profile not found! Please return to the Home page to complete onboarding.")
    st.stop()

user_name, wake_t, sleep_t, active_t, bfast_t, lunch_t, dinner_t = profile_row
sem_start = datetime.date.fromisoformat(sem_row[0]) if sem_row else datetime.date.today()
sem_end = datetime.date.fromisoformat(sem_row[1]) if sem_row else datetime.date.today() + datetime.timedelta(days=90)

# Layout: Profile edit in Col 1, Attendance offsets in Col 2
col_prof, col_offset = st.columns([1, 1])

# ── COLUMN 1: EDIT PROFILE & PREFERENCES ───────────────────
with col_prof:
    st.subheader("Edit Preferences")
    
    with st.form("edit_profile_form"):
        new_name = st.text_input("Name", value=user_name)
        
        col_w, col_s = st.columns(2)
        with col_w:
            wake_options = ["05:00 AM", "06:00 AM", "07:00 AM", "08:00 AM", "09:00 AM", "10:00 AM"]
            new_wake = st.selectbox("waking time range", wake_options, index=wake_options.index(wake_t) if wake_t in wake_options else 2)
        with col_s:
            sleep_options = ["09:00 PM", "10:00 PM", "11:00 PM", "12:00 AM", "01:00 AM", "02:00 AM"]
            new_sleep = st.selectbox("sleeping time range", sleep_options, index=sleep_options.index(sleep_t) if sleep_t in sleep_options else 2)
            
        active_options = ["Morning Focus", "Afternoon Focus", "Evening Focus", "Night Owl Focus"]
        new_active = st.selectbox("Most active study time", active_options, index=active_options.index(active_t) if active_t in active_options else 2)
        
        st.write("**Meal Timings**")
        col_bf, col_ln, col_dn = st.columns(3)
        with col_bf:
            bf_options = ["07:30 AM", "08:00 AM", "08:30 AM", "09:00 AM", "09:30 AM"]
            new_bf = st.selectbox("Breakfast Time", bf_options, index=bf_options.index(bfast_t) if bfast_t in bf_options else 1)
        with col_ln:
            ln_options = ["12:30 PM", "01:00 PM", "01:30 PM", "02:00 PM", "02:30 PM"]
            new_ln = st.selectbox("Lunch Time", ln_options, index=ln_options.index(lunch_t) if lunch_t in ln_options else 1)
        with col_dn:
            dn_options = ["07:30 PM", "08:00 PM", "08:30 PM", "09:00 PM", "09:30 PM"]
            new_dn = st.selectbox("Dinner Time", dn_options, index=dn_options.index(dinner_t) if dinner_t in dn_options else 1)
            
        st.write("**Academic Semester**")
        col_s_date, col_e_date = st.columns(2)
        with col_s_date:
            new_sem_start = st.date_input("Semester Start Date", value=new_sem_start if 'new_sem_start' in locals() else sem_start)
        with col_e_date:
            new_sem_end = st.date_input("Semester End Date", value=new_sem_end if 'new_sem_end' in locals() else sem_end)
            
        submitted_profile = st.form_submit_button("Save Profile Settings")
        if submitted_profile:
            if not new_name:
                st.error("Name cannot be empty!")
            elif new_sem_start >= new_sem_end:
                st.error("Semester end date must be after the start date!")
            else:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE user_profile 
                    SET name = ?, wake_time = ?, sleep_time = ?, active_time = ?, breakfast_time = ?, lunch_time = ?, dinner_time = ?
                    WHERE id = 1
                """, (new_name.strip(), new_wake, new_sleep, new_active, new_bf, new_ln, new_dn))
                
                cursor.execute("DELETE FROM semester")
                cursor.execute("INSERT INTO semester (start_date, end_date) VALUES (?, ?)", (str(new_sem_start), str(new_sem_end)))
                conn.commit()
                conn.close()
                st.success("Profile preferences updated successfully!")
                st.rerun()

# ── COLUMN 2: HISTORICAL ATTENDANCE OFFSETS ────────────────
with col_offset:
    st.subheader("Mid-Semester Attendance Entry")
    st.markdown("<p style='color: #94a3b8; font-size: 0.9rem; margin-top: -5px; margin-bottom: 15px;'>If you started using Orbit after classes began, enter your historical records here.</p>", unsafe_allow_html=True)
    
    if not subjects:
        st.info("No subjects found in your timetable. Please add class schedules on the Timetable Setup tab first.")
    else:
        # Fetch current offsets
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT subject, past_attended, past_total FROM attendance_offsets")
        offsets_list = cursor.fetchall()
        conn.close()
        
        offsets_dict = {subj: (att, tot) for subj, att, tot in offsets_list}
        
        # Display current historical offsets
        st.write("**Current Historical Offsets**")
        if offsets_dict:
            for subj, (att, tot) in offsets_dict.items():
                pct = (att / tot * 100) if tot > 0 else 0
                st.markdown(f"- **{subj}**: {att} / {tot} classes attended ({pct:.1f}%)")
        else:
            st.info("No historical offsets recorded yet.")
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.write("**Update Offset**")
        
        with st.form("add_attendance_offset_form"):
            selected_subject = st.selectbox("Choose Subject", subjects)
            
            # Fetch existing offset for default values
            default_att, default_tot = 0, 0
            if selected_subject in offsets_dict:
                default_att, default_tot = offsets_dict[selected_subject]
                
            past_attended_input = st.number_input("Classes Attended so far", min_value=0, value=default_att, step=1)
            past_total_input = st.number_input("Total Classes Held so far", min_value=0, value=default_tot, step=1)
            
            submitted_offset = st.form_submit_button("Save Offset Record")
            if submitted_offset:
                if past_attended_input > past_total_input:
                    st.error("Invalid input! Classes attended cannot exceed the total classes held.")
                else:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO attendance_offsets (subject, past_attended, past_total) 
                        VALUES (?, ?, ?)
                        ON CONFLICT(subject) DO UPDATE SET past_attended = excluded.past_attended, past_total = excluded.past_total
                    """, (selected_subject, past_attended_input, past_total_input))
                    conn.commit()
                    conn.close()
                    st.success(f"Historical offset updated for {selected_subject}!")
                    st.rerun()

    # ── DATA & HISTORY MANAGEMENT ──────────────────────────
    st.markdown("<hr style='border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
    st.subheader("Data & History Management")
    st.markdown("<p style='color: #94a3b8; font-size: 0.9rem; margin-top: -5px;'>Take control of your data. Clear conversation records, reset study metrics, or wipe the database entirely.</p>", unsafe_allow_html=True)
    
    col_reset_chat, col_reset_db = st.columns(2)
    
    with col_reset_chat:
        st.write("**Conversation & Distraction Logs**")
        
        # Reset Chat History
        if st.button("Reset AI Chat history", use_container_width=True):
            st.session_state["chat_history"] = [
                {"role": "assistant", "content": "Hey! How did today go? Be honest — did you get stuff done, or did you get distracted? I'm here to support you, but I won't let you slack off."}
            ]
            st.success("Chat history cleared!")
            st.rerun()
            
        # Clear Distractions
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        confirm_dist = st.checkbox("Confirm: Wipe logged distraction statistics", key="chk_clear_dist")
        if st.button("Wipe Chat Distractions & Behavioral logs", use_container_width=True, disabled=not confirm_dist):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_insights")
            conn.commit()
            conn.close()
            st.session_state["plan"] = None  # Force regenerate plan
            st.success("Logged distractions and insights deleted successfully!")
            st.rerun()
            
    with col_reset_db:
        st.write("**Academic & Tasks Data**")
        
        # Clear Tasks/Goals
        confirm_tasks = st.checkbox("Confirm: Delete all tasks and habits", key="chk_clear_tasks")
        if st.button("Delete all Tasks & Habit goals", use_container_width=True, disabled=not confirm_tasks):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks")
            cursor.execute("DELETE FROM goals")
            conn.commit()
            conn.close()
            st.session_state["plan"] = None  # Force regenerate plan
            st.success("All tasks and habits deleted!")
            st.rerun()
            
        # Clear Timetable & Attendance
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        confirm_acad = st.checkbox("Confirm: Delete all timetable & attendance logs", key="chk_clear_acad")
        if st.button("Clear Timetable & Attendance records", use_container_width=True, disabled=not confirm_acad):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM timetable")
            cursor.execute("DELETE FROM attendance")
            cursor.execute("DELETE FROM attendance_offsets")
            cursor.execute("DELETE FROM holidays")
            conn.commit()
            conn.close()
            st.session_state["plan"] = None  # Force regenerate plan
            st.success("All class timetables, holidays, and attendance records deleted!")
            st.rerun()

        # Selective History Deletion Options
        st.markdown("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
        st.write("**Selective History Deletion**")
        
        confirm_comp_tasks = st.checkbox("Confirm: Wipe completed task history", key="chk_clear_comp_tasks")
        if st.button("Delete Completed Tasks History", use_container_width=True, disabled=not confirm_comp_tasks):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE is_done = 1")
            conn.commit()
            conn.close()
            st.session_state["plan"] = None
            st.success("Completed task history deleted!")
            st.rerun()
            
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        confirm_daily = st.checkbox("Confirm: Wipe mood & sleep check-in history", key="chk_clear_daily")
        if st.button("Delete Daily Logs & Mood History", use_container_width=True, disabled=not confirm_daily):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM daily_logs")
            conn.commit()
            conn.close()
            st.session_state["plan"] = None
            st.success("Daily logs and mood history deleted!")
            st.rerun()

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        confirm_att = st.checkbox("Confirm: Wipe attendance log history", key="chk_clear_att")
        if st.button("Delete Attendance History logs", use_container_width=True, disabled=not confirm_att):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM attendance")
            conn.commit()
            conn.close()
            st.success("Attendance history logs cleared!")
            st.rerun()
            
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🚨 Factory Reset (Wipe All App Data)", expanded=False):
        st.error("Warning: This will permanently delete your user profile, configurations, tasks, notes, and historical logs. This action cannot be undone.")
        confirm_factory = st.checkbox("Yes, I understand. Wipe everything and restart onboarding.", key="chk_factory_reset")
        if st.button("FACTORY RESET ORBIT", use_container_width=True, disabled=not confirm_factory):
            conn = get_connection()
            cursor = conn.cursor()
            tables = [
                "user_profile", "semester", "tasks", "goals", "daily_logs", 
                "attendance", "attendance_offsets", "chat_insights", 
                "streaks", "rewards", "notes", "holidays"
            ]
            for t in tables:
                cursor.execute(f"DELETE FROM {t}")
            conn.commit()
            conn.close()
            
            # Reset session states
            for k in list(st.session_state.keys()):
                del st.session_state[k]
                
            st.success("Orbit has been fully reset. Restarting...")
            st.rerun()
