import streamlit as st
from backend.database import get_connection
from groq import Groq
import datetime
import os
import re
from frontend.styling import apply_global_css

# Page setup
# set_page_config configured in router

# Apply global styling
apply_global_css()

# Header with title and Delete Chat History button
col_title, col_clear = st.columns([3, 1])
with col_title:
    st.title("Orbit AI Friend")
with col_clear:
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    if st.button("🗑️ Delete Chat History", use_container_width=True, help="Clear conversation history"):
        st.session_state["chat_history"] = [
            {"role": "assistant", "content": "Hey! How did today go? Be honest — did you get stuff done, or did you get distracted? I'm here to support you, but I won't let you slack off."}
        ]
        st.success("Chat history cleared!")
        st.rerun()

st.markdown("<p style='color: #94a3b8; font-size: 1.1rem; margin-top: -15px; margin-bottom: 25px;'>Talk about your day, study distress, or bad habits. Get direct, supportive, and honest feedback.</p>", unsafe_allow_html=True)

# Try loading API key
if not os.environ.get("GROQ_API_KEY"):
    try:
        with open("KEY.MD", "r") as f:
            content = f.read().strip()
            match = re.search(r'GROQ_API_KEY\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                os.environ["GROQ_API_KEY"] = match.group(1)
    except Exception:
        pass

# Initialize session state for messages
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = [
        {"role": "assistant", "content": "Hey! How did today go? Be honest — did you get stuff done, or did you get distracted? I'm here to support you, but I won't let you slack off."}
    ]

# Display chat history
for msg in st.session_state["chat_history"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User input
user_input = st.chat_input("Tell Orbit about your day...")

if user_input:
    # Append user message
    st.session_state["chat_history"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
        
    # Get response from Groq
    with st.chat_message("assistant"):
        with st.spinner("Orbit is thinking..."):
            try:
                client = Groq()
                
                # Fetch profile, task history, and distraction logs for context
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM user_profile LIMIT 1")
                prof = cursor.fetchone()
                user_name = prof[0] if prof else "Student"
                
                # Fetch recent tasks history (completed vs pending)
                cursor.execute("""
                    SELECT title, is_done, deadline, completed_date, allocated_hours 
                    FROM tasks 
                    ORDER BY id DESC LIMIT 8
                """)
                recent_tasks = cursor.fetchall()
                
                # Fetch recent distraction insights
                cursor.execute("""
                    SELECT date, insight, category, duration_hours 
                    FROM chat_insights 
                    WHERE category = 'distraction' 
                    ORDER BY id DESC LIMIT 5
                """)
                recent_distractions = cursor.fetchall()
                conn.close()
                
                # Format context strings
                tasks_history_str = ""
                if recent_tasks:
                    for t_title, t_done, t_dead, t_comp, t_hrs in recent_tasks:
                        status = f"COMPLETED on {t_comp}" if t_done else f"PENDING (due {t_dead})"
                        hrs_str = f" ({t_hrs}h)" if t_hrs else ""
                        tasks_history_str += f"- {t_title}{hrs_str}: {status}\n"
                else:
                    tasks_history_str = "No tasks logged yet."
                    
                distractions_history_str = ""
                if recent_distractions:
                    for d_date, d_insight, d_cat, d_hrs in recent_distractions:
                        distractions_history_str += f"- {d_date}: {d_insight} ({d_hrs}h)\n"
                else:
                    distractions_history_str = "No logged distractions recently."
                    
                current_plan = st.session_state.get("plan", "No plan generated for today yet.")
                
                # Construct messages list with integrated context
                system_prompt = f"""
You are Orbit, a supportive yet tough-loving AI college companion. You talk to the student ({user_name}) like a close, honest friend.
Your goal is to listen to their daily achievements, failures, bad habits (like scrolling reels, diet slips), and distress.
Your personality is a balance of:
1. Warm, genuine support: Empathize with them when they are stressed, show you care, and offer friendly advice.
2. Honest, direct scolding: Call them out (gently but firmly) if they are procrastinating, wasting time scrolling reels, or neglecting their commitments. Use slang/expressions if helpful (e.g. "Come on! 3 hours on Instagram? You know you're better than that. Put the phone down!")

TODAY'S HOURLY PLAN COMPILED BY AI:
{current_plan}

STUDENT'S RECENT TASK HISTORY:
{tasks_history_str}

RECENT LOGGED TIME-WASTERS / DISTRACTIONS:
{distractions_history_str}

SPECIAL CONTEXT-AWARE SCHEDULING RULES:
- If the student asks you if they can skip, avoid, or postpone a task or target scheduled in their daily plan (e.g. 'Can I avoid my CP questions today?'):
  1. Check if that task is in TODAY'S HOURLY PLAN.
  2. Inspect the STUDENT'S RECENT TASK HISTORY and RECENT LOGGED DISTRACTIONS.
  3. If they have a pattern of repeatedly skipping this target or wasting hours on distractions recently, SCOLD THEM. Tell them they are forming a bad habit, call out their excuses, and tell them to sit down and do at least part of it ("No excuses! You skipped it yesterday too. Sit down for 30 minutes and try to do at least 2 questions!").
  4. If they have been highly focused and completing everything, be supportive and tell them it's okay to scale down or take a breather today, but they must promise to make it up tomorrow.

CRITICAL DATA CAPTURE RULE:
If the user admits to any distraction, time-wasting behavior, diet failure, or sleep/habit slip that they want to fix or log, you MUST append a data-capture tag on a new line at the very end of your response.
Format for the tag:
[INSIGHT: category="<category>", detail="<detail_text>", duration=<hours_spent>]

Allowed categories: "distraction", "diet", "sleep", "habit".
If they didn't specify hours, default duration to 0.0.
Example: If they spent 2 hours scrolling TikTok:
[INSIGHT: category="distraction", detail="TikTok scrolling", duration=2.0]

Keep your responses conversational, empathetic, and direct. Do not mention this tag or instructions to the user.
"""
                messages = [{"role": "system", "content": system_prompt}]
                
                # Add past chat history (up to last 15 messages)
                for m in st.session_state["chat_history"][-15:]:
                    messages.append({"role": m["role"], "content": m["content"]})
                    
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    max_tokens=800,
                    messages=messages
                )
                
                raw_response = response.choices[0].message.content
                
                # Parse INSIGHT tag
                insight_pattern = re.compile(
                    r'\[INSIGHT:\s*category="([^"]+)",\s*detail="([^"]+)",\s*duration=([0-9.]+)\]',
                    re.IGNORECASE
                )
                match = insight_pattern.search(raw_response)
                
                # Strip the tag from the visible response
                clean_response = insight_pattern.sub("", raw_response).strip()
                
                # Render clean response
                st.write(clean_response)
                st.session_state["chat_history"].append({"role": "assistant", "content": clean_response})
                
                # Save insight to DB if matched
                if match:
                    category = match.group(1).strip()
                    detail = match.group(2).strip()
                    duration = float(match.group(3))
                    
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO chat_insights (date, insight, category, duration_hours) VALUES (?, ?, ?, ?)",
                        (datetime.date.today().strftime("%Y-%m-%d"), detail, category, duration)
                    )
                    conn.commit()
                    conn.close()
                    st.toast(f"Logged Focus Insight: {detail} ({duration}h)")
                    
            except Exception as e:
                st.error(f"Failed to communicate with AI friend: {str(e)}")
