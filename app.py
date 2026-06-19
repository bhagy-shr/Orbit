import streamlit as st
from backend.database import initialize_db, get_connection

# Initialize database tables
initialize_db()

# Page config (must be called ONLY once at the entrypoint)
st.set_page_config(
    page_title="Orbit",
    page_icon="○",
    layout="wide"
)

# Helper to check onboarding status
def check_onboarding():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT onboarded FROM user_profile LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row is not None and row[0] == 1

onboarded = check_onboarding()

if not onboarded:
    # ONLY onboarding page is visible when not onboarded
    pages = [
        st.Page("onboarding.py", title="Welcome", icon="🪐")
    ]
else:
    # All pages are visible once onboarding is complete
    pages = [
        st.Page("home.py", title="Home", icon="🪐"),
        st.Page("pages/1_Tasks_Goals.py", title="Tasks & Goals", icon="📋"),
        st.Page("pages/2_Timetable.py", title="Timetable & Attendance", icon="📅"),
        st.Page("pages/3_Notes.py", title="Notes", icon="📝"),
        st.Page("pages/4_Rewards.py", title="Rewards", icon="🏆"),
        st.Page("pages/5_Chatbot.py", title="AI Chat Companion", icon="💬"),
        st.Page("pages/6_Analysis.py", title="Weekly Analysis", icon="📈"),
        st.Page("pages/7_Profile.py", title="My Profile", icon="⚙️"),
        st.Page("pages/8_Logout.py", title="Logout", icon="🚪")
    ]

pg = st.navigation(pages)
pg.run()
