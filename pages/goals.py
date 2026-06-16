import streamlit as st
from backend.database import get_connection
import backend.database as database
import datetime
from frontend.styling import apply_global_css

# Page configuration
st.set_page_config(page_title="Goals", page_icon="○", layout='wide')

# Apply global styling
apply_global_css()

st.title("Goals & Streaks")
st.markdown("<p style='color: #94a3b8; font-size: 1.1rem; margin-top: -15px; margin-bottom: 25px;'>Set recurring habits and track your daily consistency streak.</p>", unsafe_allow_html=True)

st.subheader("Add Recurring Goal")
st.markdown("<p style='color: #94a3b8; font-size: 0.9rem; margin-top: -5px;'>These are habits you want to build — things you do every day or week.</p>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    goal_title = st.text_input("Goal Title", placeholder="e.g. 10 DSA questions")
with col2:
    frequency = st.selectbox("Frequency", ["Daily", "Weekly"])
with col3:
    target = st.text_input("Target", placeholder="e.g. 30 mins, 10 questions")

if st.button("Add Goal"):
    if goal_title and target:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO goals (title, frequency, target) VALUES (?,?,?)",
            (goal_title, frequency, target)
        )
        conn.commit()
        conn.close()
        st.success(f"Goal added: {goal_title}")
        st.rerun()
    else:
        st.error('Please fill in all fields!')

st.markdown("<hr style='border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

st.subheader("Your Goals")

conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT id, title, frequency, target FROM goals")
goals = cursor.fetchall()
conn.close()

if goals:
    for goal in goals:
        goal_id, title, frequency, target = goal
        st.markdown('<div class="task-checkbox-container">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
        with col1:
            st.write(f"**{title}**")
        with col2:
            st.write(f"{frequency}")
        with col3:
            st.write(f"Target: {target}")
        with col4:
            if st.button("Delete", key=f"del_goal_{goal_id}"):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
                conn.commit()
                conn.close()
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("No goals yet — add your first goal above!")

st.markdown("<hr style='border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

# ── STREAK TRACKER ───────────────────────────────────────
st.subheader("Your Streak")
st.markdown("<p style='color: #94a3b8; font-size: 0.9rem; margin-top: -5px;'>Log your check-in every day to build your streak.</p>", unsafe_allow_html=True)

conn = get_connection()
cursor = conn.cursor()
# Get all streak entries ordered by date
cursor.execute("SELECT date, streak_count FROM streaks ORDER BY date DESC")
streaks = cursor.fetchall()
conn.close()

today = datetime.date.today().strftime("%Y-%m-%d")
yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

# Calculate current streak
current_streak = 0
if streaks:
    latest_date, latest_count = streaks[0]
    if latest_date == today or latest_date == yesterday:
        current_streak = latest_count

# Show streak display
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Current Streak", f"{current_streak} days")
with col2:
    if streaks:
        st.metric("Last Check-in", streaks[0][0])
    else:
        st.metric("Last Check-in", "Never")
with col3:
    max_streak = max([s[1] for s in streaks]) if streaks else 0
    st.metric("Best Streak", f"{max_streak} days")

st.markdown("<br>", unsafe_allow_html=True)

if st.button("Log Today's Check-in"):
    conn = get_connection()
    cursor = conn.cursor()

    # Check if already logged today
    cursor.execute("SELECT id FROM streaks WHERE date = ?", (today,))
    existing = cursor.fetchone()

    if existing:
        st.warning("Already logged today! Come back tomorrow.")
    else:
        # Check if yesterday was logged to continue streak
        cursor.execute(
            "SELECT streak_count FROM streaks WHERE date = ?",
            (yesterday,)
        )
        yesterday_streak = cursor.fetchone()

        if yesterday_streak:
            new_streak = yesterday_streak[0] + 1
        else:
            new_streak = 1

        cursor.execute(
            "INSERT INTO streaks (date, streak_count) VALUES (?, ?)",
            (today, new_streak)
        )
        conn.commit()
        conn.close()

        st.success(f"Streak logged! You're on a {new_streak} day streak!")
        st.rerun()

# ── STREAK MILESTONES ────────────────────────────────────
st.markdown("<hr style='border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
st.subheader("Streak Milestones")

milestones = {
    3: "Rest Pass — guilt-free skincare or hobby time",
    7: "New app theme unlocked",
    10: "Sleep Pass — guilt-free early bedtime",
    14: "Orbit Star badge earned",
    30: "Orbit Legend status achieved"
}

for days, reward in milestones.items():
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        st.write(f"**{days} days**")
    with col2:
        st.write(reward)
    with col3:
        if current_streak >= days:
            st.markdown("<span style='color: #10b981; font-weight: 500;'>Unlocked</span>", unsafe_allow_html=True)
        else:
            remaining = days - current_streak
            st.write(f"{remaining} days left")