import streamlit as st
from backend.database import get_connection
import datetime
from frontend.styling import apply_global_css

# Page configuration
st.set_page_config(
    page_title="Personal Notes",
    page_icon="○",
    layout="wide"
)

# Apply global styling
apply_global_css()

# Initialize session states
if "selected_note_id" not in st.session_state:
    st.session_state["selected_note_id"] = "new"

st.title("Personal Notes")
st.markdown("<p style='color: #94a3b8; font-size: 1.1rem; margin-top: -15px; margin-bottom: 25px;'>Write down study plans, course notes, and personal ideas in Markdown.</p>", unsafe_allow_html=True)

# 2-Column layout: Notes list sidebar & Note content editor/viewer
col_list, col_editor = st.columns([1, 2])

# ── COLUMN 1: NOTES LIST SIDEBAR ───────────────────────────
with col_list:
    st.subheader("My Notes")
    
    # New note trigger
    if st.button("+ Create New Note", use_container_width=True):
        st.session_state["selected_note_id"] = "new"
        st.rerun()
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Search notes
    search_query = st.text_input("Search notes", placeholder="Type title or content...")
    
    # Fetch notes list from database
    conn = get_connection()
    cursor = conn.cursor()
    if search_query:
        cursor.execute(
            "SELECT id, title, updated_at FROM notes WHERE title LIKE ? OR content LIKE ? ORDER BY updated_at DESC",
            (f"%{search_query}%", f"%{search_query}%")
        )
    else:
        cursor.execute("SELECT id, title, updated_at FROM notes ORDER BY updated_at DESC")
    notes_list = cursor.fetchall()
    conn.close()
    
    # Render note list cards
    if notes_list:
        for note_id, note_title, note_updated in notes_list:
            # Format update date cleanly
            try:
                dt = datetime.datetime.fromisoformat(note_updated)
                date_str = dt.strftime("%b %d, %Y - %I:%M %p")
            except ValueError:
                date_str = note_updated
                
            active_style = "border-color: #4f46e5; background: rgba(79, 70, 229, 0.05);" if st.session_state["selected_note_id"] == note_id else ""
            
            # Clickable card select mechanism
            st.markdown(
                f"""
                <div class="custom-card" style="padding: 12px; margin-bottom: 8px; cursor: pointer; {active_style}">
                    <div style="font-weight: 500; font-size: 0.95rem; color: #ffffff;">{note_title}</div>
                    <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 3px;">Updated: {date_str}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Invisible Streamlit button over the card to handle click
            if st.button("Open", key=f"open_note_{note_id}", use_container_width=True):
                st.session_state["selected_note_id"] = note_id
                st.rerun()
    else:
        st.info("No notes found. Create your first note above!")

# ── COLUMN 2: NOTE CONTENT EDITOR & PREVIEW ────────────────
with col_editor:
    selected_id = st.session_state["selected_note_id"]
    
    if selected_id == "new":
        st.subheader("Create New Note")
        
        note_title = st.text_input("Title", placeholder="e.g. Chemistry Notes - Chapter 1")
        note_content = st.text_area("Content (supports Markdown)", height=350, placeholder="Write your notes here...")
        
        if st.button("Save Note"):
            if note_title:
                now_str = datetime.datetime.now().isoformat()
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO notes (title, content, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (note_title.strip(), note_content, now_str, now_str)
                )
                conn.commit()
                # Set active note to the new saved note ID
                new_id = cursor.lastrowid
                conn.close()
                
                st.session_state["selected_note_id"] = new_id
                st.success("Note saved successfully!")
                st.rerun()
            else:
                st.error("Please enter a note title!")
                
    else:
        # Load note from database
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT title, content, created_at, updated_at FROM notes WHERE id = ?", (selected_id,))
        note_data = cursor.fetchone()
        conn.close()
        
        if note_data:
            title_val, content_val, created_val, updated_val = note_data
            
            # Render tabs for Edit and Live Markdown Preview
            tab_edit, tab_preview = st.tabs(["Edit Note", "Preview Markdown"])
            
            with tab_edit:
                edited_title = st.text_input("Title", value=title_val)
                edited_content = st.text_area("Content (supports Markdown)", value=content_val, height=350)
                
                col_btn_save, col_btn_del = st.columns([4, 1])
                with col_btn_save:
                    if st.button("Save Changes"):
                        if edited_title:
                            now_str = datetime.datetime.now().isoformat()
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE notes SET title = ?, content = ?, updated_at = ? WHERE id = ?",
                                (edited_title.strip(), edited_content, now_str, selected_id)
                            )
                            conn.commit()
                            conn.close()
                            st.success("Changes saved!")
                            st.rerun()
                        else:
                            st.error("Note title cannot be empty!")
                            
                with col_btn_del:
                    if st.button("Delete Note", key=f"del_note_{selected_id}"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM notes WHERE id = ?", (selected_id,))
                        conn.commit()
                        conn.close()
                        st.session_state["selected_note_id"] = "new"
                        st.success("Note deleted!")
                        st.rerun()
                        
            with tab_preview:
                st.markdown(f"### {title_val}")
                st.markdown("<hr style='border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
                if content_val:
                    st.markdown(content_val)
                else:
                    st.markdown("*Note is empty. Go to 'Edit Note' to write content.*")
        else:
            st.error("Selected note could not be found.")
            st.session_state["selected_note_id"] = "new"
            st.rerun()
