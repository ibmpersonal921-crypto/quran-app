"""
app.py
------
Entry point for the Streamlit multipage app. This file ONLY sets up
navigation — the actual Home/Dashboard content lives in
app_pages/0_🏠_Home.py, just like every other page.

Run with:  streamlit run app.py
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

# IMPORTANT: these paths must exactly match the filenames inside
# app_pages/ (case-sensitive, emoji included, no trailing spaces).
pages = [
    st.Page("app_pages/0_🏠_Home.py", title="Home", icon="🏠", default=True),
    st.Page("app_pages/1_📖_Browse_Quran.py", title="Browse Quran", icon="📖"),
    st.Page("app_pages/2_🤖_AI_Companion.py", title="AI Companion", icon="🤖"),
    st.Page("app_pages/3_🎙️_Recitation_Coach.py", title="Recitation Coach", icon="🎙️"),
    st.Page("app_pages/4_⚙️_Settings.py", title="Settings", icon="⚙️"),
]

nav = st.navigation(pages)
nav.run()
