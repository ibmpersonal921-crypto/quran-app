"""
app.py
------
Entry point for the Streamlit multipage app. This file ONLY sets up
navigation — the actual Home/Dashboard content lives in
pages/0_Home.py, just like every other page.

NOTE: page filenames are plain ASCII on purpose (no emoji) because
emoji in filenames get corrupted/mismatched when pushed through
GitHub/Streamlit Cloud. Emoji still show in the sidebar via icon=.

Run with:  streamlit run app.py
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

pages = [
    st.Page("pages/0_Home.py", title="Home", icon="🏠", default=True),
    st.Page("pages/1_Browse_Quran.py", title="Browse Quran", icon="📖"),
    st.Page("pages/2_AI_Companion.py", title="AI Companion", icon="🤖"),
    st.Page("pages/3_Recitation_Coach.py", title="Recitation Coach", icon="🎙️"),
    st.Page("pages/4_Settings.py", title="Settings", icon="⚙️"),
]

nav = st.navigation(pages)
nav.run()
