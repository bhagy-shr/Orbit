import streamlit as st

def apply_global_css():
    """Applies a premium dark-galaxy theme, custom cards, custom buttons,
    and styles for timelines and checkoff items across the app."""
    
    st.markdown(
        """
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        
        <style>
        /* Global font override */
        html, body, [class*="css"], .stMarkdown {
            font-family: 'Outfit', sans-serif !important;
        }
        
        /* Modernized background and styling */
        .stApp {
            background-color: #0d0e15;
            color: #e2e8f0;
        }
        
        /* Custom Header and Text Styling */
        h1, h2, h3, h4, h5, h6 {
            color: #ffffff !important;
            font-weight: 600 !important;
            letter-spacing: -0.02em;
        }
        
        /* Glassmorphic Metrics Card */
        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 15px 20px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(5px);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            border-color: rgba(108, 92, 231, 0.3);
        }
        div[data-testid="stMetricLabel"] {
            color: #94a3b8 !important;
            font-size: 0.85rem !important;
            font-weight: 500 !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        div[data-testid="stMetricValue"] {
            color: #ffffff !important;
            font-size: 1.8rem !important;
            font-weight: 700 !important;
        }
        
        /* Modern Buttons */
        div.stButton > button {
            background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%) !important;
            color: #ffffff !important;
            border: none !important;
            padding: 8px 20px !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15) !important;
            transition: all 0.2s ease !important;
        }
        div.stButton > button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 16px rgba(79, 70, 229, 0.3) !important;
            filter: brightness(1.1);
        }
        div.stButton > button:active {
            transform: translateY(1px) !important;
        }
        
        /* Dangerous or secondary buttons */
        div.stButton > button[key*="del"], div.stButton > button[key*="trash"] {
            background: rgba(239, 68, 68, 0.1) !important;
            color: #ef4444 !important;
            border: 1px solid rgba(239, 68, 68, 0.2) !important;
            box-shadow: none !important;
        }
        div.stButton > button[key*="del"]:hover, div.stButton > button[key*="trash"]:hover {
            background: #ef4444 !important;
            color: #ffffff !important;
        }
        
        /* Streamlit default block overrides */
        .stTextInput input, .stTextArea textarea, .stSelectbox select, .stDateInput input, .stTimeInput input {
            background-color: #171923 !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            font-size: 0.95rem !important;
        }
        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: #4f46e5 !important;
            box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2) !important;
        }
        
        /* Custom Card container for items */
        .custom-card {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        }
        
        /* Vertical Timeline CSS */
        .timeline {
            position: relative;
            margin: 15px 0;
            padding-left: 24px;
        }
        .timeline::before {
            content: '';
            position: absolute;
            top: 6px;
            left: 5px;
            bottom: 6px;
            width: 2px;
            background: linear-gradient(180deg, #4f46e5 0%, #3b82f6 100%);
        }
        .timeline-item {
            position: relative;
            margin-bottom: 20px;
        }
        .timeline-item:last-child {
            margin-bottom: 0;
        }
        .timeline-dot {
            position: absolute;
            width: 10px;
            height: 10px;
            left: -23px;
            top: 7px;
            background: #4f46e5;
            border-radius: 50%;
            border: 2px solid #0d0e15;
            box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
        }
        .timeline-content {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 12px 16px;
            transition: all 0.2s ease;
        }
        .timeline-content:hover {
            border-color: rgba(79, 70, 229, 0.3);
            background: rgba(255, 255, 255, 0.04);
        }
        .timeline-time {
            font-size: 0.75rem;
            font-weight: 600;
            color: #60a5fa;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 3px;
        }
        .timeline-activity {
            font-size: 0.9rem;
            font-weight: 400;
            color: #f1f5f9;
        }
        
        /* Clean checklist styling */
        .task-checkbox-container {
            display: flex;
            align-items: center;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 8px;
            padding: 10px 15px;
            margin-bottom: 10px;
            transition: all 0.2s ease;
        }
        .task-checkbox-container:hover {
            border-color: rgba(255, 255, 255, 0.15);
            background: rgba(255, 255, 255, 0.04);
        }
        
        /* Hide default Streamlit footer */
        footer {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        header {background: transparent !important;}
        </style>
        """,
        unsafe_allow_html=True
    )
