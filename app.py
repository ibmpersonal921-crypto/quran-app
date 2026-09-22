"""
app.py
------
Entry point for the Streamlit app. Sets page config once, then hands off
to st.navigation() with explicit titles/icons for every page — this is
what gives the sidebar clean labels ("Home", "Browse Quran", ...) instead
of Streamlit's default behavior of showing the raw filename ("app") for
the main script.

Run with:  streamlit run app.py
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from config import APP_NAME, APP_ICON, APP_TAGLINE
from database import db

st.set_page_config(page_title=f"{APP_NAME} — Dashboard", page_icon=APP_ICON, layout="wide")
db.init_db()

pages = [
    st.Page("app_pages/0_🏠_Home.py", title="Home", icon="🏠", default=True),
    st.Page("app_pages/1_📖_Browse_Quran.py", title="Browse Quran", icon="📖"),
    st.Page("app_pages/2_🤖_AI_Companion.py", title="AI Companion", icon="🤖"),
    st.Page("app_pages/3_🎙️_Recitation_Coach.py", title="Recitation Coach", icon="🎙️"),
    st.Page("app_pages/4_⚙️_Settings.py", title="Settings", icon="⚙️"),
]

pg = st.navigation(pages, position="sidebar")
pg.run()
