"""
app.py
------
Entry point for the Streamlit multipage app. This file IS the "Home /
Dashboard" page shown in the reference screenshot; the rest of the app
lives in pages/ (Streamlit auto-detects and lists them in the sidebar).

Run with:  streamlit run app.py
"""

import streamlit as st

from config import APP_NAME, APP_TAGLINE, APP_ICON, DAILY_GOAL_POINTS
from utils.helpers import inject_css, page_header, compute_streak
from database import db
from services import quran_api

st.set_page_config(page_title=f"{APP_NAME} — Dashboard", page_icon=APP_ICON, layout="wide")
db.init_db()
inject_css()

# ---------------------------------------------------------------------------
# Sidebar branding (matches the reference UI: logo, name, tagline)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:2px;">
            <span style="font-size:1.8rem;">{APP_ICON}</span>
            <div>
                <div style="font-weight:700;font-size:1.05rem;color:#f4f7f5;">{APP_NAME}</div>
                <div style="font-size:0.78rem;color:#7e9186;">{APP_TAGLINE}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<hr class='qsc-divider'/>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header + search-to-AI shortcut
# ---------------------------------------------------------------------------
top_l, top_r = st.columns([3, 2])
with top_l:
    page_header("Dashboard", "Welcome back — here's your study space for today.", "🏠")
with top_r:
    st.write("")
    quick_q = st.text_input(
        "search", placeholder="Search or ask AI (e.g., 'Al-Fatiha tafsir')",
        label_visibility="collapsed",
    )
    if quick_q:
        st.session_state["prefill_chat_question"] = quick_q
        st.info("Open **AI Companion** in the sidebar — your question is ready there. 🤖")

# ---------------------------------------------------------------------------
# Stat pills: streak, points, goals done today
# ---------------------------------------------------------------------------
completion_dates = db.get_all_completion_dates()
streak = compute_streak(completion_dates)
total_points = db.get_total_points()
points_today = db.get_points_today()
goals_today = db.get_goals_for_date()
done_today = sum(1 for g in goals_today if g["is_done"])

s1, s2, s3, s4 = st.columns(4)
stats = [
    (s1, "🔥", streak, "Day Streak"),
    (s2, "⭐", total_points, "Total Points"),
    (s3, "✅", f"{done_today}/{len(goals_today)}", "Goals Today"),
    (s4, "➕", points_today, "Points Today"),
]
for col, emoji, value, label in stats:
    with col:
        st.markdown(
            f"""<div class="qsc-stat"><div class="value">{emoji} {value}</div>
            <div class="label">{label}</div></div>""",
            unsafe_allow_html=True,
        )
