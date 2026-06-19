import streamlit as st
from backend.database import get_connection
from frontend.styling import apply_global_css
import datetime

apply_global_css()

st.title("🪐 Welcome to Orbit")
st.markdown("<p style='color: #94a3b8; font-size: 1.1rem; margin-top: -15px; margin-bottom: 25px;'>Set up your profile to calibrate your personalized academic schedules.</p>", unsafe_allow_html=True)

with st.form("onboarding_form"):
    st.subheader("Personal Details")
    user_name = st.text_input("What should we call you?", placeholder="e.g. Alex")
    
    st.subheader("Daily Timing Routine")
    col1, col2, col3 = st.columns(3)
    with col1:
        wake_time = st.selectbox(
            "waking time range", 
            ["05:00", "06:00", "07:00", "08:00", "09:00", "10:00"]
        )
    with col2:
        sleep_time = st.selectbox(
            "sleeping time range", 
            ["21:00", "22:00", "23:00", "00:00", "01:00", "02:00"]
        )
    with col3:
        active_time = st.selectbox(
            "Most active study time",
            ["Morning Focus", "Afternoon Focus", "Evening Focus", "Night Owl Focus"]
        )
        
    st.subheader("Meal Schedules")
    col_b, col_l, col_d = st.columns(3)
    with col_b:
        breakfast_t = st.selectbox("Breakfast time", ["07:00", "07:30", "08:00", "08:30", "09:00", "09:30"])
    with col_l:
        lunch_t = st.selectbox("Lunch time", ["12:00", "12:30", "13:00", "13:30", "14:00", "14:30"])
    with col_d:
        dinner_t = st.selectbox("Dinner time", ["19:00", "19:30", "20:00", "20:30", "21:00", "21:30"])
        
    st.subheader("Academic Semester Configuration")
    col_start, col_end = st.columns(2)
    with col_start:
        sem_start = st.date_input("Semester Start Date", value=datetime.date.today() - datetime.timedelta(days=30))
    with col_end:
        sem_end = st.date_input("Semester End Date", value=datetime.date.today() + datetime.timedelta(days=90))
        
    submitted = st.form_submit_button("Launch Orbit")
    if submitted:
        if not user_name:
            st.error("Please enter your name to personalize the companion!")
        elif sem_start >= sem_end:
            st.error("Semester end date must be after the start date!")
        else:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_profile (name, wake_time, sleep_time, active_time, breakfast_time, lunch_time, dinner_time, onboarded)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (user_name.strip(), wake_time, sleep_time, active_time, breakfast_t, lunch_t, dinner_t))
            
            cursor.execute("DELETE FROM semester")
            cursor.execute("INSERT INTO semester (start_date, end_date) VALUES (?, ?)", (str(sem_start), str(sem_end)))
            
            cursor.execute("INSERT INTO streaks (date, streak_count) VALUES (?, 0)", (str(datetime.date.today()),))
            conn.commit()
            conn.close()
            st.success("Welcome aboard! Let's get started.")
            st.rerun()
