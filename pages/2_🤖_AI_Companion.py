import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from config import APP_NAME
from utils.helpers import inject_css, page_header, render_sidebar_branding, render_sidebar_settings
from database import db
from services import ai_chat

db.init_db()
inject_css()

with st.sidebar:
    render_sidebar_branding()
render_sidebar_settings()

page_header("AI Companion", "Ask about a verse, a hadith, or a topic — grounded in real sources.", "🤖")

st.caption("Answers come from a language model and can be wrong. Verify anything you act on against a published tafsir or a qualified scholar.")

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {"role": m["role"], "content": m["content"]} for m in db.get_chat_history(limit=40)
    ]

for msg in st.session_state.chat_messages:
    avatar = "🧠" if msg["role"] == "assistant" else "🙂"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

prefill = st.session_state.pop("prefill_chat_question", None)
user_input = st.chat_input("Ask about a verse, a word, or its context")
if prefill and not user_input:
    user_input = prefill

if user_input:
    st.session_state.chat_messages.append({"role": "user", "content": user_input})
    db.log_chat("user", user_input)
    with st.chat_message("user", avatar="🙂"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🧠"):
        with st.spinner("Checking sources..."):
            result = ai_chat.ask(user_input, st.session_state.chat_messages[:-1])
        st.markdown(result["answer"])
        if result["grounded"]:
            st.caption("✅ Grounded in verified Quran/Hadith text fetched live for this answer.")

    st.session_state.chat_messages.append({"role": "assistant", "content": result["answer"]})
    db.log_chat("assistant", result["answer"], sources=result.get("context_used", ""))

if st.button("Clear conversation"):
    st.session_state.chat_messages = []
    db.clear_chat_history()
    st.rerun()

st.markdown('<div class="qsc-card qsc-card-tight">', unsafe_allow_html=True)
st.markdown('<span class="qsc-label">Try asking</span>', unsafe_allow_html=True)
ex1, ex2, ex3 = st.columns(3)
examples = [
    "What is the meaning of Surah Al-Asr?",
    "Tell me Bukhari hadith 1",
    "What does 2:255 say?",
]
for col, ex in zip([ex1, ex2, ex3], examples):
    with col:
        st.button(ex, key=f"ex_{ex}", on_click=lambda e=ex: st.session_state.update(prefill_chat_question=e))
st.markdown("</div>", unsafe_allow_html=True)
