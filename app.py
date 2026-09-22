"""
app.py
Entry point for the Streamlit app.
"""
import streamlit as st
from config import APP_NAME, APP_ICON
from database import db

st.set_page_config(page_title=f"{APP_NAME} — Dashboard", page_icon=APP_ICON, layout="wide")
db.init_db()

# IMPORTANT: Filenames here MUST match your GitHub files exactly (NO EMOJIS in filenames)
pages = [
    st.Page("app_pages/0_Home.py", title="Home", icon="🏠", default=True),
    st.Page("app_pages/1_Browse_Quran.py", title="Browse Quran", icon="📖"),
    st.Page("app_pages/2_AI_Companion.py", title="AI Companion", icon=""),
    st.Page("app_pages/3_Recitation_Coach.py", title="Recitation Coach", icon="🎙️"),
    st.Page("app_pages/4_Settings.py", title="Settings", icon="⚙️"),
]

pg = st.navigation(pages, position="sidebar")
pg.run()
