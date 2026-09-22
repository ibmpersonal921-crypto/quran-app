import streamlit as st

from config import APP_NAME
from utils.helpers import inject_css, page_header
from database import db
from services import ai_chat

st.set_page_config(page_title=f"{APP_NAME} — AI Companion", page_icon="🤖", layout="wide")
db.init_db()
inject_css()

page_header("AI Companion", "Ask about a verse, a hadith, or a topic — grounded in real sources.", "🤖")

st.markdown(
    """
    <div class="qsc-card qsc-card-tight" style="border-color:rgba(212,175,55,0.35);">
    ℹ️ I fetch the actual Arabic text of any ayah or hadith you reference before answering,
    so quotes are accurate. For fiqh rulings I present the mainstream scholarly views rather
    than a single verdict — for a binding personal ruling, please consult a qualified scholar.
    </div>
    """,
    unsafe_allow_html=True,
)

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {"role": m["role"], "content": m["content"]} for m in db.get_chat_history(limit=40)
    ]

for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "🧕"):
        st.markdown(msg["content"])

prefill = st.session_state.pop("prefill_chat_question", None)
user_input = st.chat_input("Ask me anything about the Quran or Hadith...")
if prefill and not user_input:
    user_input = prefill

if user_input:
    st.session_state.chat_messages.append({"role": "user", "content": user_input})
    db.log_chat("user", user_input)
    with st.chat_message("user", avatar="🧕"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Checking sources..."):
            result = ai_chat.ask(user_input, st.session_state.chat_messages[:-1])
        st.markdown(result["answer"])
        if result["grounded"]:
            st.caption("✅ Grounded in verified Quran/Hadith text fetched live for this answer.")
        with st.expander("Clear this chat"):
            if st.button("🗑️ Clear conversation"):
                st.session_state.chat_messages = []
                db.clear_chat_history()
                st.rerun()

    st.session_state.chat_messages.append({"role": "assistant", "content": result["answer"]})
    db.log_chat("assistant", result["answer"], sources=result.get("context_used", ""))

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
