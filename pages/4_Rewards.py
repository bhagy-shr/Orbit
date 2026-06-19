import streamlit as st
from backend.database import get_connection
import datetime
from frontend.styling import apply_global_css

# Page configuration
# set_page_config configured in router

# Apply global styling
apply_global_css()

st.title("Rewards")
st.markdown("<p style='color: #94a3b8; font-size: 1.1rem; margin-top: -15px; margin-bottom: 25px;'>Earn consistent check-in streak badges and unlock college passes.</p>", unsafe_allow_html=True)

# ── GET CURRENT STREAK ───────────────────────────────────
conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT streak_count FROM streaks ORDER BY date DESC LIMIT 1")
streak_row = cursor.fetchone()
current_streak = streak_row[0] if streak_row else 0
conn.close()

# ── REWARD DEFINITIONS ───────────────────────────────────
rewards = [
    {
        "id": "rest_pass",
        "days": 3,
        "title": "Rest Pass",
        "description": "You've earned guilt-free hobby or personal time. No studying allowed!",
        "label": "REST"
    },
    {
        "id": "theme_unlock",
        "days": 7,
        "title": "New Theme",
        "description": "You've unlocked the Dark Galaxy theme for Orbit!",
        "label": "THEME"
    },
    {
        "id": "sleep_pass",
        "days": 10,
        "title": "Sleep Pass",
        "description": "Guilt-free early bedtime tonight. You've earned it!",
        "label": "SLEEP"
    },
    {
        "id": "star_badge",
        "days": 14,
        "title": "Orbit Star",
        "description": "You're a certified Orbit Star. 14 days of consistency!",
        "label": "STAR"
    },
    {
        "id": "legend",
        "days": 30,
        "title": "Orbit Legend",
        "description": "30 days. You're unstoppable. Orbit Legend status achieved!",
        "label": "LEGEND"
    }
]

# ── STREAK DISPLAY ───────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.metric("Current Streak", f"{current_streak} days")
with col2:
    # Find next milestone
    next_milestone = None
    for reward in rewards:
        if current_streak < reward["days"]:
            next_milestone = reward
            break
    if next_milestone:
        days_left = next_milestone["days"] - current_streak
        st.metric(
            "Next Reward",
            next_milestone["title"],
            f"{days_left} days away"
        )
    else:
        st.metric("Status", "All rewards unlocked! 🎉")

st.markdown("<hr style='border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

# ── REWARDS GRID ─────────────────────────────────────────
st.subheader("Your Rewards")

for reward in rewards:
    unlocked = current_streak >= reward["days"]

    if unlocked:
        # Save to database if not already saved
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM rewards WHERE reward_name = ?", (reward["id"],))
        exists = cursor.fetchone()
        if not exists:
            cursor.execute(
                "INSERT INTO rewards (reward_name, unlocked_at, is_unlocked) VALUES (?, ?, 1)",
                (reward["id"], reward["days"])
            )
            conn.commit()
        conn.close()

        st.markdown(
            f"""
            <div class="custom-card" style="border-left: 4px solid #10b981; padding: 16px; margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: 600; font-size: 1.1rem; color: #ffffff;">{reward['title']}</div>
                        <div style="font-size: 0.9rem; color: #cbd5e1; margin-top: 5px;">{reward['description']}</div>
                        <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 5px; font-style: italic;">Unlocked at a {reward['days']}-day streak</div>
                    </div>
                    <div style="font-weight: 600; font-size: 0.9rem; color: #10b981; background: rgba(16, 185, 129, 0.1); padding: 4px 10px; border-radius: 4px;">UNLOCKED</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        days_left = reward["days"] - current_streak
        st.markdown(
            f"""
            <div class="custom-card" style="border-left: 4px solid #475569; padding: 16px; margin-bottom: 15px; opacity: 0.6;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: 600; font-size: 1.1rem; color: #94a3b8;">{reward['title']} (Locked)</div>
                        <div style="font-size: 0.9rem; color: #64748b; margin-top: 5px;">Reach a {reward['days']}-day streak to unlock.</div>
                    </div>
                    <div style="font-weight: 600; font-size: 0.85rem; color: #94a3b8; background: rgba(71, 85, 105, 0.1); padding: 4px 10px; border-radius: 4px;">{days_left} DAYS LEFT</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# ── MOTIVATION ───────────────────────────────────────────
st.markdown("<hr style='border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
st.subheader("Keep Going!")

if current_streak == 0:
    st.info("Start your streak today — log your first check-in on the Goals page!")
elif current_streak < 3:
    st.info(f"Just {3 - current_streak} more days to your first reward! You've got this.")
elif current_streak < 7:
    st.success(f"{current_streak} days strong! Rest Pass unlocked — keep going for the theme unlock!")
elif current_streak < 14:
    st.success(f"{current_streak} days! You're in the top tier of consistency. Orbit Star is close!")
else:
    st.success(f"{current_streak} days!! You're an Orbit Legend in the making!")
