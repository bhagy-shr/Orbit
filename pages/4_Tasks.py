import streamlit as st
from backend.database import get_connection
import datetime
import plotly.graph_objects as go
from frontend.styling import apply_global_css

# Page configuration
st.set_page_config(page_title="Tasks", page_icon="○", layout="wide")

# Apply global styling
apply_global_css()

st.title("Tasks & Deadlines")
st.markdown("<p style='color: #94a3b8; font-size: 1.1rem; margin-top: -15px; margin-bottom: 25px;'>Track and manage your homework, assignments, and goals.</p>", unsafe_allow_html=True)

# ── ADD TASK ────────────────────────────────────────────
st.subheader("Add New Task")

col1, col2, col3 = st.columns(3)
with col1:
    title = st.text_input("Task Title", placeholder="e.g. History essay")
with col2:
    deadline = st.date_input("Deadline")
with col3:
    task_type = st.selectbox("Priority / Type", [
        "High Priority",
        "Medium Priority",
        "Low Priority",
        "Club / Extracurricular",
        "Personal Goal"
    ])

if st.button("Add Task"):
    if title:
        # DB compatibility mapping
        db_type_map = {
            "High Priority": "🔴 High Priority",
            "Medium Priority": "🔵 Medium Priority",
            "Low Priority": "🟡 Low Priority",
            "Club / Extracurricular": "🎯 Club / Extracurricular",
            "Personal Goal": "💙 Personal Goal"
        }
        db_type = db_type_map.get(task_type, task_type)
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (title, deadline, task_type, is_done) VALUES (?, ?, ?, 0)",
            (title, str(deadline), db_type)
        )
        conn.commit()
        conn.close()
        st.success(f"Task added: {title}")
        st.rerun()
    else:
        st.error("Please enter a task title!")

st.markdown("<hr style='border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

# ── TASK LIST ───────────────────────────────────────────
st.subheader("Your Tasks")

conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT id, title, deadline, task_type, is_done FROM tasks ORDER BY deadline")
tasks = cursor.fetchall()
conn.close()

today = datetime.date.today()

if tasks:
    for task in tasks:
        task_id, title, deadline, task_type, is_done = task
        deadline_date = datetime.date.fromisoformat(deadline)
        days_left = (deadline_date - today).days

        clean_type = task_type.replace("🔴 ", "").replace("🔵 ", "").replace("🟡 ", "").replace("🎯 ", "").replace("💙 ", "")

        st.markdown('<div class="task-checkbox-container">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            done = st.checkbox(
                f"{clean_type} | {title}",
                value=bool(is_done),
                key=f"task_{task_id}"
            )
            if done != bool(is_done):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE tasks SET is_done = ? WHERE id = ?",
                    (1 if done else 0, task_id)
                )
                conn.commit()
                conn.close()
                st.rerun()

        with col2:
            if is_done:
                st.markdown("<span style='color: #10b981; font-weight: 500;'>Completed</span>", unsafe_allow_html=True)
            elif days_left < 0:
                st.markdown(f"<span style='color: #ef4444; font-weight: 500;'>Overdue by {abs(days_left)} days</span>", unsafe_allow_html=True)
            elif days_left == 0:
                st.markdown("<span style='color: #f59e0b; font-weight: 500;'>Due today</span>", unsafe_allow_html=True)
            elif days_left <= 2:
                st.markdown(f"<span style='color: #3b82f6;'>{days_left} days left</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color: #94a3b8;'>{days_left} days left</span>", unsafe_allow_html=True)

        with col3:
            if st.button("Delete", key=f"del_{task_id}"):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                conn.commit()
                conn.close()
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("No tasks yet — add your first task above!")

st.markdown("<hr style='border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

# ── PIE CHART ───────────────────────────────────────────
st.subheader("Task Overview")

conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT deadline, task_type, is_done FROM tasks")
all_tasks = cursor.fetchall()
conn.close()

if all_tasks:
    completed = 0
    high_risk = 0
    mild_risk = 0
    low_priority = 0

    for deadline, task_type, is_done in all_tasks:
        if is_done:
            completed += 1
        else:
            deadline_date = datetime.date.fromisoformat(deadline)
            days_left = (deadline_date - today).days
            if days_left <= 0:
                high_risk += 1
            elif days_left <= 2:
                mild_risk += 1
            else:
                low_priority += 1

    labels = ["Completed", "High Risk", "Mild Risk", "Low Priority"]
    values = [completed, high_risk, mild_risk, low_priority]
    colors = ["#10b981", "#ef4444", "#3b82f6", "#64748b"]

    # Remove zero values
    filtered = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]
    if filtered:
        labels, values, colors = zip(*filtered)
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors),
            hole=0.4
        )])
        fig.update_layout(
            title="Task Completion Breakdown",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white", family="Outfit"),
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Add tasks to see your status overview!")