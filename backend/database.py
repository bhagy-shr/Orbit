import sqlite3

def get_connection():
    conn = sqlite3.connect("orbit.db")
    return conn

def initialize_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Timetable - stores subjects and their class times
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            day TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL
        )
    """)

    # Tasks - assignments, club events, personal commitments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            deadline TEXT,
            task_type TEXT,
            is_done INTEGER DEFAULT 0,
            allocated_hours REAL,
            pref_start_time TEXT,
            pref_end_time TEXT,
            completed_date TEXT
        )
    """)

    # Upgrade tasks table if it already exists without new columns
    for col_name, col_type in [
        ("allocated_hours", "REAL"),
        ("pref_start_time", "TEXT"),
        ("pref_end_time", "TEXT"),
        ("completed_date", "TEXT")
    ]:
        try:
            cursor.execute(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass  # Column already exists

    # Goals - recurring daily/weekly habits
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            frequency TEXT NOT NULL,
            target TEXT NOT NULL
        )
    """)

    # Daily logs - mood, sleep, date
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            mood INTEGER NOT NULL,
            sleep REAL NOT NULL,
            feedback TEXT
        )
    """)

    # Attendance - per subject tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    # Holidays - semester holidays and breaks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS holidays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            reason TEXT
        )
    """)

    # Semester info - start and end dates
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS semester (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL
        )
    """)

    # Streaks - tracking daily check-in streaks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS streaks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            streak_count INTEGER DEFAULT 0
        )
    """)

    # Rewards - unlocked rewards
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reward_name TEXT NOT NULL,
            unlocked_at INTEGER NOT NULL,
            is_unlocked INTEGER DEFAULT 0
        )
    """)

    # Notes - personal notes for user
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # User profile - stores onboarding & schedule preference info
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            wake_time TEXT,
            sleep_time TEXT,
            active_time TEXT,
            breakfast_time TEXT,
            lunch_time TEXT,
            dinner_time TEXT,
            onboarded INTEGER DEFAULT 0
        )
    """)

    # Attendance offsets - stores pre-recorded classes for mid-semester users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance_offsets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT UNIQUE NOT NULL,
            past_attended INTEGER DEFAULT 0,
            past_total INTEGER DEFAULT 0
        )
    """)

    # Chat insights - logs user habits/distractions from the chatbot page
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            insight TEXT NOT NULL,
            category TEXT,
            duration_hours REAL DEFAULT 0.0
        )
    """)

    conn.commit()
    conn.close()

def escalate_task_priorities():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, deadline, task_type FROM tasks WHERE is_done = 0")
    rows = cursor.fetchall()
    
    import datetime
    today = datetime.date.today()
    for row_id, deadline_str, task_type in rows:
        if deadline_str:
            try:
                deadline_dt = datetime.date.fromisoformat(deadline_str)
                days_left = (deadline_dt - today).days
                if days_left <= 2:
                    if "High" not in task_type:
                        new_type = "🔴 High Priority"
                        cursor.execute("UPDATE tasks SET task_type = ? WHERE id = ?", (new_type, row_id))
            except ValueError:
                pass
    conn.commit()
    conn.close()

# Initialize the database immediately when imported by any module
initialize_db()
try:
    escalate_task_priorities()
except Exception:
    pass
