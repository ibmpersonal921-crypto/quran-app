"""
app.py
Entry point for the Streamlit app. Sets page config once, then hands off
to st.navigation() with explicit titles/icons for every page.
"""
import sys
from pathlib import Path

# Fix 1: Changed Path(file) to Path(__file__)
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
from config import APP_NAME, APP_ICON
from database import db

st.set_page_config(page_title=f"{APP_NAME} — Dashboard", page_icon=APP_ICON, layout="wide")
db.init_db()

# Fix 2: Changed folder to "app_pages/" 
# Fix 3: Removed all trailing spaces from the strings
pages = [
    st.Page("app_pages/0__Home.py", title="Home", icon="", default=True),
    st.Page("app_pages/1_📖_Browse_Quran.py", title="Browse Quran", icon="📖"),
    st.Page("app_pages/2__AI_Companion.py", title="AI Companion", icon="🤖"),
    st.Page("app_pages/3_🎙️_Recitation_Coach.py", title="Recitation Coach", icon="🎙️"),
    st.Page("app_pages/4_⚙️_Settings.py", title="Settings", icon="⚙️"),
]

pg = st.navigation(pages, position="sidebar")
pg.run()
