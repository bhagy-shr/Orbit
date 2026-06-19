import streamlit as st
from backend.database import get_connection, get_local_today
import datetime
import pandas as pd
from frontend.styling import apply_global_css

# Page setup
# set_page_config configured in router

# Apply global styling
apply_global_css()

# Helper function for attendance calculation
def calculate_total_classes(subject, start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor()

    # Get which days this subject is scheduled
    cursor.execute(
        "SELECT DISTINCT day FROM timetable WHERE subject = ?",
        (subject,)
    )
    class_days = [row[0] for row in cursor.fetchall()]

    # Get all holidays
    cursor.execute("SELECT date FROM holidays")
    holidays = [row[0] for row in cursor.fetchall()]
    conn.close()

    # Count classes between start and end date
    total = 0
    current = start_date
    while current <= end_date:
        day_name = current.strftime("%A")
        if day_name in class_days:
            if current.strftime("%Y-%m-%d") not in holidays:
                total += 1
        current += datetime.timedelta(days=1)

    return total

st.title("Timetable & Attendance")
st.markdown("<p style='color: #94a3b8; font-size: 1.1rem; margin-top: -15px; margin-bottom: 25px;'>Manage class schedules, set semester dates, and track your attendance requirements.</p>", unsafe_allow_html=True)

# Tabs for Timetable vs Attendance
tab_timetable, tab_attendance = st.tabs(["Timetable & Semester Setup", "Attendance Tracker"])

# ──────────────────────────────────────────────────────────
# TAB 1: TIMETABLE & SEMESTER SETUP
# ──────────────────────────────────────────────────────────
with tab_timetable:
    # Top row: Semester Dates & Holidays
    col_sem, col_hol = st.columns(2)
    
    with col_sem:
        st.subheader("Semester Dates")
        
        # Load existing semester dates
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT start_date, end_date FROM semester")
        sem_row = cursor.fetchone()
        conn.close()
        
        default_start = get_local_today()
        default_end = get_local_today() + datetime.timedelta(days=120)
        
        if sem_row:
            try:
                default_start = datetime.date.fromisoformat(sem_row[0])
                default_end = datetime.date.fromisoformat(sem_row[1])
            except ValueError:
                pass
                
        with st.form("semester_dates_form"):
            start_date = st.date_input("Semester Start Date", value=default_start)
            end_date = st.date_input("Semester End Date", value=default_end)
            if st.form_submit_button("Save Semester Dates"):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM semester")
                cursor.execute(
                    "INSERT INTO semester (start_date, end_date) VALUES (?, ?)",
                    (str(start_date), str(end_date))
                )
                conn.commit()
                conn.close()
                
                # Also update user profile dates to sync
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE user_profile SET onboarded = 1 WHERE id = 1") # Ensure onboarded stays active
                conn.commit()
                conn.close()
                
                st.success("Semester dates saved!")
                st.rerun()

    with col_hol:
        st.subheader("Add Holiday")
        with st.form("holiday_form", clear_on_submit=True):
            holiday_date = st.date_input("Holiday Date")
            holiday_reason = st.text_input("Reason (e.g. Diwali, Thanksgiving)")
            if st.form_submit_button("Add Holiday"):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO holidays (date, reason) VALUES (?, ?)",
                    (str(holiday_date), holiday_reason)
                )
                conn.commit()
                conn.close()
                st.success(f"Holiday added for {holiday_date}!")
                st.rerun()
                
        # Show existing holidays in clean layout
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, date, reason FROM holidays ORDER BY date")
        holidays_list = cursor.fetchall()
        conn.close()
        
        if holidays_list:
            st.write("**Holidays:**")
            for h_id, h_date, h_reason in holidays_list:
                col_h_text, col_h_del = st.columns([5, 1])
                with col_h_text:
                    st.write(f"- {h_date} — {h_reason}")
                with col_h_del:
                    if st.button("Delete", key=f"del_hol_{h_id}"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM holidays WHERE id = ?", (h_id,))
                        conn.commit()
                        conn.close()
                        st.success("Deleted!")
                        st.rerun()

    st.markdown("<hr style='border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
    
    # Bottom section: Timetable Editor
    st.subheader("Timetable Editor")
    st.markdown("<p style='color: #94a3b8; font-size: 0.9rem; margin-top: -5px; margin-bottom: 15px;'>Manage your weekly class schedule in the table below. Use the bottom row to add new classes, double click cells to edit, or select a row and hit Delete on your keyboard.</p>", unsafe_allow_html=True)
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, subject, day, start_time, end_time FROM timetable")
    classes_rows = cursor.fetchall()
    conn.close()
    
    # Build dataframe for data_editor
    df_classes = pd.DataFrame(classes_rows, columns=["id", "Subject", "Day", "Start Time", "End Time"])
    
    days_options = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    edited_df = st.data_editor(
        df_classes,
        column_config={
            "id": None, # Hide ID
            "Subject": st.column_config.TextColumn("Subject Name", required=True),
            "Day": st.column_config.SelectboxColumn("Day of Week", options=days_options, required=True),
            "Start Time": st.column_config.TextColumn("Start Time (e.g. 09:00:00)", required=True),
            "End Time": st.column_config.TextColumn("End Time (e.g. 10:30:00)", required=True)
        },
        num_rows="dynamic",
        key="timetable_sheet_editor",
        use_container_width=True
    )
    
    if st.button("Save Timetable Changes"):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM timetable")
        df_clean = edited_df.fillna("")
        for idx, row in df_clean.iterrows():
            subj = str(row["Subject"]).strip()
            day_val = str(row["Day"]).strip()
            st_time = str(row["Start Time"]).strip()
            en_time = str(row["End Time"]).strip()
            if subj and day_val and st_time and en_time:
                cursor.execute(
                    "INSERT INTO timetable (subject, day, start_time, end_time) VALUES (?, ?, ?, ?)",
                    (subj, day_val, st_time, en_time)
                )
        conn.commit()
        conn.close()
        st.success("Weekly timetable updated successfully!")
        st.rerun()
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Weekly Schedule View
    st.subheader("Weekly Schedule Preview")
    df_preview_clean = edited_df.fillna("")
    days_cols = st.columns(3)
    for i, d in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]):
        col = days_cols[i % 3]
        with col:
            st.markdown(f"**{d}**")
            day_classes = df_preview_clean[df_preview_clean["Day"] == d]
            if not day_classes.empty:
                day_classes_sorted = day_classes.sort_values(by="Start Time")
                for _, row in day_classes_sorted.iterrows():
                    st.markdown(
                        f"""
                        <div class="custom-card" style="padding: 12px; margin-bottom: 10px;">
                            <div style="font-weight: 500; font-size: 0.95rem; color: #ffffff;">{row['Subject']}</div>
                            <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 3px;">{row['Start Time']} — {row['End Time']}</div>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
            else:
                st.markdown("<p style='color: #64748b; font-size: 0.85rem; font-style: italic;'>No classes scheduled</p>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────
# TAB 2: ATTENDANCE TRACKER
# ──────────────────────────────────────────────────────────
with tab_attendance:
    # Load unique subjects from database
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT subject FROM timetable")
    subjects = [row[0] for row in cursor.fetchall()]
    conn.close()

    if not subjects:
        st.info("No subjects found in your timetable. Please add classes in the 'Timetable Setup' tab first.")
    else:
        col_mark, col_bunk = st.columns([1, 1])
        
        with col_mark:
            st.subheader("Mark Attendance")
            with st.form("mark_attendance_form", clear_on_submit=True):
                selected_subject = st.selectbox("Select Subject", subjects)
                selected_date = st.date_input("Date", value=get_local_today())
                selected_status = st.selectbox("Status", ["Present", "Absent"])
                
                if st.form_submit_button("Save Attendance Record"):
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT id FROM attendance WHERE subject = ? AND date = ?",
                        (selected_subject, str(selected_date))
                    )
                    existing = cursor.fetchone()
                    
                    if existing:
                        st.warning(f"Attendance record already exists for {selected_subject} on {selected_date}!")
                    else:
                        cursor.execute(
                            "INSERT INTO attendance (subject, date, status) VALUES (?, ?, ?)",
                            (selected_subject, str(selected_date), selected_status)
                        )
                        conn.commit()
                        st.success(f"Marked {selected_status} for {selected_subject} on {selected_date}")
                    conn.close()
                    st.rerun()

        with col_bunk:
            st.subheader("Bunk Calculator")
            st.markdown("<p style='color: #94a3b8; font-size: 0.9rem; margin-top: -5px; margin-bottom: 15px;'>Calculate safe bunks based on your schedule, attendance offsets, and target.</p>", unsafe_allow_html=True)
            
            selected_bunk_subject = st.selectbox("Choose Subject", subjects, key="bunk_subject_select")
            
            # Fetch semester dates
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT start_date, end_date FROM semester")
            semester_row = cursor.fetchone()
            conn.close()
            
            # Calculate total expected classes
            if semester_row:
                start_dt = datetime.date.fromisoformat(semester_row[0])
                end_dt = min(
                    datetime.date.fromisoformat(semester_row[1]),
                    get_local_today()
                )
                total_classes = calculate_total_classes(selected_bunk_subject, start_dt, end_dt)
            else:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM attendance WHERE subject = ?", (selected_bunk_subject,))
                total_classes = cursor.fetchone()[0]
                conn.close()
                
            # Fetch historical offsets
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT past_attended, past_total FROM attendance_offsets WHERE subject = ?", (selected_bunk_subject,))
            offset_row = cursor.fetchone()
            conn.close()
            
            offset_att = offset_row[0] if offset_row else 0
            offset_tot = offset_row[1] if offset_row else 0
            
            total_classes += offset_tot
            
            # Calculate attended classes
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM attendance WHERE subject = ? AND status = 'Present'",
                (selected_bunk_subject,)
            )
            attended_classes = cursor.fetchone()[0] + offset_att
            conn.close()
            
            if total_classes > 0:
                pct = (attended_classes / total_classes) * 100
                st.write(f"Current stats: **{attended_classes}** attended out of **{total_classes}** classes (offset + logs) (**{pct:.1f}%**)")
                
                safe_bunks = int((attended_classes - 0.75 * total_classes) / 0.75)
                if safe_bunks > 0:
                    st.success(f"You can safely bunk next **{safe_bunks}** classes of {selected_bunk_subject} and stay above 75% target.")
                else:
                    needed = 0
                    curr_att = attended_classes
                    curr_tot = total_classes
                    while (curr_att / curr_tot) < 0.75:
                        needed += 1
                        curr_att += 1
                        curr_tot += 1
                    st.error(f"You need to attend next **{needed}** consecutive classes of {selected_bunk_subject} to reach 75% target.")
            else:
                st.info("No classes scheduled yet. Ensure semester dates are set and attendance is marked.")

        st.markdown("<hr style='border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
        
        # Attendance Summary list
        st.subheader("Attendance Summary")
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT start_date, end_date FROM semester")
        semester_row = cursor.fetchone()
        conn.close()
        
        # Display summary in clean grid cards
        sum_cols = st.columns(3)
        for idx, subj in enumerate(subjects):
            col = sum_cols[idx % 3]
            
            if semester_row:
                start_dt = datetime.date.fromisoformat(semester_row[0])
                end_dt = min(
                    datetime.date.fromisoformat(semester_row[1]),
                    get_local_today()
                )
                subj_total = calculate_total_classes(subj, start_dt, end_dt)
            else:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM attendance WHERE subject = ?", (subj,))
                subj_total = cursor.fetchone()[0]
                conn.close()
                
            # Fetch offset
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT past_attended, past_total FROM attendance_offsets WHERE subject = ?", (subj,))
            offset_row = cursor.fetchone()
            conn.close()
            
            offset_att = offset_row[0] if offset_row else 0
            offset_tot = offset_row[1] if offset_row else 0
            
            subj_total += offset_tot
            
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM attendance WHERE subject = ? AND status = 'Present'",
                (subj,)
            )
            subj_attended = cursor.fetchone()[0] + offset_att
            conn.close()
            
            with col:
                if subj_total > 0:
                    subj_pct = (subj_attended / subj_total) * 100
                    
                    if subj_pct < 75:
                        status_msg = "⚠️ Below 75% threshold!"
                        status_color = "#ef4444"
                    elif subj_pct < 85:
                        status_msg = "🟡 Caution: close to limit"
                        status_color = "#f59e0b"
                    else:
                        status_msg = "✅ Good Standing"
                        status_color = "#10b981"
                        
                    st.markdown(
                        f"""
                        <div class="custom-card" style="padding: 16px; border-left: 4px solid {status_color};">
                            <div style="font-weight: 600; font-size: 1.1rem; color: #ffffff;">{subj}</div>
                            <div style="font-size: 0.9rem; color: #94a3b8; margin: 8px 0 12px 0;">
                                Classes Attended: {subj_attended} / {subj_total}<br>
                                Attendance Rate: <b>{subj_pct:.1f}%</b>
                            </div>
                            <div style="font-size: 0.85rem; font-weight: 500; color: {status_color};">{status_msg}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"""
                        <div class="custom-card" style="padding: 16px; border-left: 4px solid #64748b;">
                            <div style="font-weight: 600; font-size: 1.1rem; color: #ffffff;">{subj}</div>
                            <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 8px; font-style: italic;">No classes expected yet</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
