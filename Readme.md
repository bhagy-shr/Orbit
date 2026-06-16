app.py is what Streamlit runs first — it's your home/landing page
database.py keeps all data logic in one place — clean and easy to debug
utils/ai.py keeps the Groq API call separate — so you can improve it without touching the rest of the app
pages/ is a Streamlit convention — every .py file you put here automatically becomes a new page in your app