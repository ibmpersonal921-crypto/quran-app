"""
app.py
Entry point for the Streamlit app. Sets page config and navigation.
"""
import streamlit as st
from config import APP_NAME, APP_ICON
from database import db

st.set_page_config(page_title=f"{APP_NAME} — Dashboard", page_icon=APP_ICON, layout="wide")
db.init_db()

# IMPORTANT: These filenames must EXACTLY match the files inside your 'app_pages' folder on GitHub!
pages = [
    st.Page("app_pages/0_🏠_Home.py", title="Home", icon="🏠", default=True),
    st.Page("app_pages/1_📖_Browse_Quran.py", title="Browse Quran", icon="📖"),
    st.Page("app_pages/2_🤖_AI_Companion.py", title="AI Companion", icon="🤖"),
    st.Page("app_pages/3_🎙️_Recitation_Coach.py", title="Recitation Coach", icon="🎙️"),
    st.Page("app_pages/4_⚙️_Settings.py", title="Settings", icon="⚙️"),
]

pg = st.navigation(pages, position="sidebar")
pg.run()
