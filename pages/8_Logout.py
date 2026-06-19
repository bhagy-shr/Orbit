import streamlit as st
from backend.database import get_connection
from frontend.styling import apply_global_css

# Page setup
# set_page_config configured in router

# Apply global styling
apply_global_css()

st.title("🪐 Logout & Wipe Data")
st.markdown("<p style='color: #94a3b8; font-size: 1.1rem; margin-top: -15px; margin-bottom: 25px;'>Reset your profile and clear all logged data from Orbit.</p>", unsafe_allow_html=True)

# Warning block
st.markdown(
    """
    <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.35); padding: 25px; border-radius: 12px; margin-bottom: 25px;">
        <h3 style="color: #ef4444; margin-top: 0; margin-bottom: 10px;">⚠️ CRITICAL WARNING: Complete Data Deletion</h3>
        <p style="color: #fca5a5; font-size: 1.05rem; line-height: 1.6; margin-bottom: 0;">
            Logging out of Orbit will permanently wipe <b>all your personal profile configurations, study timetable, class schedules, attendance logs, notes, goals, streaks, and chatbot conversation records</b>. 
            This action is irreversible and no data will be retained.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.write("Please confirm your intention to delete all profile data below:")

confirm_checkbox = st.checkbox("Yes, I understand. I want to delete all my data and reset Orbit.", key="logout_confirm_chk")

col_btn, _ = st.columns([1, 2])
with col_btn:
    if st.button("DELETE ALL DATA & LOGOUT", use_container_width=True, type="primary", disabled=not confirm_checkbox):
        with st.spinner("Wiping database..."):
            conn = get_connection()
            cursor = conn.cursor()
            tables = [
                "user_profile", "semester", "tasks", "goals", "daily_logs", 
                "attendance", "attendance_offsets", "chat_insights", 
                "streaks", "rewards", "notes", "holidays"
            ]
            for t in tables:
                try:
                    cursor.execute(f"DELETE FROM {t}")
                except Exception:
                    pass  # Skip if table does not exist yet
            conn.commit()
            conn.close()
            
            # Reset all session state keys
            for k in list(st.session_state.keys()):
                del st.session_state[k]
                
            st.success("Successfully logged out and wiped all local profile data. Redirecting...")
            st.rerun()
