import streamlit as st
from backend.database import get_connection
import datetime
import plotly.graph_objects as go
from frontend.styling import apply_global_css

# Page setup
# set_page_config configured in router

# Apply global styling
apply_global_css()

st.title("Weekly Analytics & Insights")
st.markdown("<p style='color: #94a3b8; font-size: 1.1rem; margin-top: -15px; margin-bottom: 25px;'>A 7-day retrospective of your productivity metrics, focus habits, and distractions.</p>", unsafe_allow_html=True)

# Helper: Get dates for past 7 days
today = datetime.date.today()
past_7_days = [today - datetime.timedelta(days=i) for i in range(6, -1, -1)]
past_7_dates_str = [d.strftime("%Y-%m-%d") for d in past_7_days]

conn = get_connection()
cursor = conn.cursor()

# ── 1. COMPUTE TASK COMPLETIONS FOR THE PAST 7 DAYS ─────
daily_task_stats = []
for d in past_7_days:
    date_str = d.strftime("%Y-%m-%d")
    # Total tasks due on this date
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE deadline = ?", (date_str,))
    total_due = cursor.fetchone()[0]
    # Tasks due on this date that are completed
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE deadline = ? AND is_done = 1", (date_str,))
    completed_due = cursor.fetchone()[0]
    
    daily_task_stats.append({
        "date": d,
        "date_str": date_str,
        "total": total_due,
        "completed": completed_due
    })

# ── 2. COMPUTE DISTRACTIONS FOR THE PAST 7 DAYS ─────────
seven_days_ago_str = past_7_dates_str[0]
cursor.execute("""
    SELECT insight, SUM(duration_hours) 
    FROM chat_insights 
    WHERE date >= ? AND category = 'distraction'
    GROUP BY insight
""", (seven_days_ago_str,))
distractions_data = cursor.fetchall()

# ── 3. COMPUTE FOCUS STUDY TIME & ATTENDANCE HELD ───────
# Total task focus hours completed in past week
cursor.execute("""
    SELECT SUM(allocated_hours) 
    FROM tasks 
    WHERE is_done = 1 AND completed_date >= ?
""", (seven_days_ago_str,))
study_hours_row = cursor.fetchone()
total_study_hours = study_hours_row[0] if study_hours_row and study_hours_row[0] else 0.0

# Total class slots marked present in past week
cursor.execute("""
    SELECT COUNT(*) 
    FROM attendance 
    WHERE status = 'Present' AND date >= ?
""", (seven_days_ago_str,))
classes_present_count = cursor.fetchone()[0]
conn.close()

# Layout: Col 1 for Metrics & Task completions, Col 2 for charts
col_stats, col_charts = st.columns([1, 1])

# ── COLUMN 1: Retrospective list & Core Metrics ───────────
with col_stats:
    st.subheader("Retrospective Review")
    st.markdown("<p style='color: #94a3b8; font-size: 0.9rem; margin-top: -5px; margin-bottom: 15px;'>Review daily quest completions over the past week.</p>", unsafe_allow_html=True)
    
    # Render daily checklist outcomes
    for stat in daily_task_stats:
        d = stat["date"]
        total = stat["total"]
        comp = stat["completed"]
        day_name = d.strftime("%A, %b %d")
        
        if total == 0:
            status_text = "No quests scheduled"
            badge = "⚪"
            style_cls = "border-color: rgba(255, 255, 255, 0.04); background: rgba(255, 255, 255, 0.01);"
        elif comp == total:
            status_text = f"All quests completed! ({comp}/{total})"
            badge = "🟢"
            style_cls = "border-color: rgba(16, 185, 129, 0.2); background: rgba(16, 185, 129, 0.03);"
        else:
            status_text = f"Failed to complete all quests ({comp} completed out of {total} due)"
            badge = "🔴"
            style_cls = "border-color: rgba(239, 68, 68, 0.2); background: rgba(239, 68, 68, 0.03);"
            
        st.markdown(
            f"""
            <div class="custom-card" style="padding: 12px; margin-bottom: 10px; {style_cls}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-weight: 600; font-size: 0.95rem; color: #ffffff;">{day_name}</div>
                    <div style="font-size: 1.1rem;">{badge}</div>
                </div>
                <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px;">{status_text}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

# ── COLUMN 2: Visual Charts & Analytics ────────────────────
with col_charts:
    st.subheader("Behavioral & Focus Analytics")
    st.markdown("<p style='color: #94a3b8; font-size: 0.9rem; margin-top: -5px; margin-bottom: 15px;'>Review where your time went and what distractions cost you study hours.</p>", unsafe_allow_html=True)
    
    # 2 Metrics side by side
    col_met1, col_met2 = st.columns(2)
    with col_met1:
        st.metric("Focused Study Time", f"{total_study_hours:.1f} hrs")
    with col_met2:
        st.metric("Classes Attended", f"{classes_present_count} sessions")
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.write("**Distraction Breakdown**")
    
    if distractions_data:
        labels = [row[0] for row in distractions_data]
        values = [row[1] for row in distractions_data]
        
        # Plotly Pie Chart
        fig = go.Figure(data=[go.Pie(
            labels=labels, 
            values=values, 
            hole=.4,
            marker=dict(colors=['#6366f1', '#a855f7', '#ec4899', '#f43f5e', '#eab308']),
            textinfo='label+percent',
            textposition='inside',
            insidetextorientation='radial'
        )])
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0', family='Outfit'),
            showlegend=False,
            margin=dict(t=10, b=10, l=10, r=10),
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No logged distractions in the past 7 days. Keep up the high focus!")
