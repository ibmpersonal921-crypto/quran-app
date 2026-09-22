import streamlit as st

from config import APP_NAME, RECITERS, TRANSLATION_EDITIONS, FEEDBACK_LANGUAGES, ANTHROPIC_API_KEY
from utils.helpers import inject_css, page_header
from database import db

st.set_page_config(page_title=f"{APP_NAME} — Settings", page_icon="⚙️", layout="wide")
db.init_db()
inject_css()

page_header("Settings", "Your preferences, saved locally.", "⚙️")

st.markdown('<div class="qsc-card">', unsafe_allow_html=True)
st.markdown('<span class="qsc-label">Preferences</span>', unsafe_allow_html=True)

default_reciter = db.get_setting("default_reciter", "Mishary Rashid Alafasy")
default_translation = db.get_setting("default_translation", "English — Saheeh International")
default_feedback_lang = db.get_setting("default_feedback_lang", "English")

reciter = st.selectbox("Default reciter", list(RECITERS.keys()), index=list(RECITERS.keys()).index(default_reciter) if default_reciter in RECITERS else 0)
translation = st.selectbox("Default translation", list(TRANSLATION_EDITIONS.values()), index=list(TRANSLATION_EDITIONS.values()).index(default_translation) if default_translation in TRANSLATION_EDITIONS.values() else 0)
feedback_lang = st.selectbox("Default recitation feedback voice", list(FEEDBACK_LANGUAGES.keys()), index=list(FEEDBACK_LANGUAGES.keys()).index(default_feedback_lang) if default_feedback_lang in FEEDBACK_LANGUAGES else 0)

if st.button("💾 Save preferences"):
    db.set_setting("default_reciter", reciter)
    db.set_setting("default_translation", translation)
    db.set_setting("default_feedback_lang", feedback_lang)
    st.success("Saved!")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="qsc-card">', unsafe_allow_html=True)
st.markdown('<span class="qsc-label">AI Companion status</span>', unsafe_allow_html=True)
if ANTHROPIC_API_KEY:
    st.success("✅ Claude API key detected — AI Companion is active.")
else:
    st.warning(
        "⚠️ No `ANTHROPIC_API_KEY` found. Add one to your `.env` file to enable the AI "
        "Companion chatbot. See the README for how to get a key."
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
