import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from config import APP_NAME, AI_PROVIDER, GEMINI_API_KEY, ANTHROPIC_API_KEY
from utils.helpers import inject_css, page_header, render_sidebar_branding, render_sidebar_settings
from database import db

st.set_page_config(page_title=f"{APP_NAME} — Settings", page_icon="⚙️", layout="wide")
db.init_db()
inject_css()

with st.sidebar:
    render_sidebar_branding()
render_sidebar_settings()

page_header("Settings", "Your preferences, saved locally.", "⚙️")
st.caption("Reciter, translation, text size, and transliteration live in the ⚙️ Settings panel in the sidebar — they apply everywhere and stick as you navigate.")

st.markdown('<div class="qsc-card">', unsafe_allow_html=True)
st.markdown('<span class="qsc-label">AI Companion status</span>', unsafe_allow_html=True)
if AI_PROVIDER == "anthropic":
    if ANTHROPIC_API_KEY:
        st.success("✅ Claude API key detected — AI Companion is active (paid, Claude).")
    else:
        st.warning(
            "AI_PROVIDER is set to `anthropic` but no `ANTHROPIC_API_KEY` was found, or your "
            "credit balance is at $0. Add credits at console.anthropic.com/settings/billing, "
            "or switch AI_PROVIDER back to `gemini` for the free tier."
        )
else:
    if GEMINI_API_KEY:
        st.success("✅ Gemini API key detected — AI Companion is active (free tier).")
    else:
        st.warning(
            "No `GEMINI_API_KEY` found. Get a free one (no card needed) at aistudio.google.com, "
            "then add it to your local `.env` or your Streamlit Cloud app's Secrets panel."
        )
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="qsc-card">', unsafe_allow_html=True)
st.markdown('<span class="qsc-label">Danger zone</span>', unsafe_allow_html=True)
st.caption("This clears your local goals, streak, chat history, and recitation history. This cannot be undone.")
if st.button("🗑️ Reset all my progress"):
    st.session_state["confirm_reset"] = True
if st.session_state.get("confirm_reset"):
    st.error("Are you sure? This will delete everything.")
    yc, nc = st.columns(2)
    with yc:
        if st.button("Yes, reset everything"):
            with db.get_conn() as conn:
                conn.executescript(
                    "DELETE FROM goals; DELETE FROM completion_log; "
                    "DELETE FROM chat_history; DELETE FROM recitation_sessions;"
                )
            st.session_state.clear()
            st.success("All progress reset.")
            st.rerun()
    with nc:
        if st.button("Cancel"):
            st.session_state["confirm_reset"] = False
            st.rerun()
st.markdown("</div>", unsafe_allow_html=True)
