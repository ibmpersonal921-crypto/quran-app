import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import streamlit.components.v1 as components

from config import APP_NAME, FEEDBACK_LANGUAGES, DAILY_GOAL_POINTS
from utils.helpers import inject_css, page_header, render_sidebar_branding, render_sidebar_settings
from database import db
from services import quran_api, recitation_coach, tts

db.init_db()
inject_css()

with st.sidebar:
    render_sidebar_branding()
settings = render_sidebar_settings()

page_header("Recitation Coach", "Recite an ayah, get instant word-by-word correction.", "🎙️")

surahs = quran_api.get_surah_list()
if not surahs:
    st.error("Couldn't load the surah list — check your internet connection and reload.")
    st.stop()

c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    surah_labels = [f"{s['number']}. {s['englishName']} ({s['name']})" for s in surahs]
    default_idx = next((i for i, s in enumerate(surahs) if s["number"] == 1), 0)
    surah_choice = st.selectbox("Surah to practice", surah_labels, index=default_idx)
    surah_number = int(surah_choice.split(".")[0])
    ayah_count = next(s["numberOfAyahs"] for s in surahs if s["number"] == surah_number)
with c2:
    ayah_number = st.number_input("Ayah #", min_value=1, max_value=ayah_count, value=1, step=1)
with c3:
    feedback_lang_label = st.selectbox("Feedback voice", list(FEEDBACK_LANGUAGES.keys()), index=2)
    feedback_lang = FEEDBACK_LANGUAGES[feedback_lang_label]

reference = quran_api.get_ayah_multilang(surah_number, ayah_number)
if not reference.get("arabic"):
    st.warning("Couldn't load this ayah.")
    st.stop()

# ---------------------------------------------------------------------------
# Reference recitation
# ---------------------------------------------------------------------------
st.markdown('<div class="qsc-card">', unsafe_allow_html=True)
badge_col, text_col = st.columns([0.6, 6])
with badge_col:
    st.markdown(f'<div class="qsc-ayah-badge">{ayah_number}</div>', unsafe_allow_html=True)
with text_col:
    st.markdown(
        f'<div class="arabic-text" style="font-size:{settings["arabic_size"]+4}px;">{reference["arabic"]}</div>',
        unsafe_allow_html=True,
    )
    if settings["show_translit"] and reference.get("transliteration"):
        st.markdown(f'<p style="color:#b9c9c0;font-style:italic;">{reference["transliteration"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="color:#f4f7f5;">{reference.get("english","")}</p>', unsafe_allow_html=True)

st.markdown(f'<span class="qsc-label">Reference recitation — {settings["reciter_name"]}</span>', unsafe_allow_html=True)
st.audio(
    quran_api.get_ayah_audio_url(reference["global_ayah_number"], settings["reciter_id"]),
    format="audio/mp3",
)
st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Live Voice Call — free, browser-based, speaks back to you in real time
# ---------------------------------------------------------------------------
st.markdown('<span class="qsc-label">📞 Live Voice Call — free</span>', unsafe_allow_html=True)
st.caption(
    "Recites along with you continuously and talks back with spoken coaching, live — powered entirely "
    "by your browser's built-in speech recognition + speech synthesis, so it's free with no API key and "
    "no server round-trip. Needs Chrome or Edge. It's a live *practice partner*, not a tajweed examiner — "
    "no service, free or paid, can judge makhraj/tajweed the way a human teacher can. Practice Mode below "
    "is the more precise, fully-tested scoring path."
)
components.html(
    recitation_coach.build_live_mode_html(reference["arabic"], feedback_lang=feedback_lang),
    height=280,
)

st.write("")

# ---------------------------------------------------------------------------
# Optional upgrade: continuous WebRTC + Deepgram (paid after free trial credit)
# ---------------------------------------------------------------------------
from services import live_stream_coach

with st.expander("⚙️ Optional upgrade: sturdier live streaming via Deepgram (paid after a free trial credit)"):
    st.caption(
        "The call above already gives you live, free voice coaching. This upgrade swaps the browser's "
        "recognizer for Deepgram's — steadier connection, works in more browsers, lower latency — but "
        "Deepgram is a paid API past its free trial credit, so it's opt-in, not required."
    )
    if not live_stream_coach.is_configured():
        st.info(
            "Not set up yet. Needs a free-trial **Deepgram** API key (console.deepgram.com), then add "
            "`DEEPGRAM_API_KEY` to your secrets/.env, plus `pip install streamlit-webrtc deepgram-sdk av numpy`. "
            "See README for exact steps."
        )
    else:
        from streamlit_webrtc import webrtc_streamer, WebRtcMode
        from streamlit_autorefresh import st_autorefresh

        session_key = f"live_session_{surah_number}_{ayah_number}"
        session = live_stream_coach.get_or_create_session(session_key, reference["arabic"])

        def _audio_frame_callback(frame):
            try:
                pcm = live_stream_coach.audio_frame_to_pcm16(frame)
                session.push_audio(pcm)
            except Exception:
                pass
            return frame

        webrtc_streamer(
            key=f"webrtc_{session_key}",
            mode=WebRtcMode.SENDONLY,
            audio_frame_callback=_audio_frame_callback,
            media_stream_constraints={"audio": True, "video": False},
        )

        st_autorefresh(interval=700, key=f"refresh_{session_key}")
        st.markdown(f'<div class="arabic-text">{live_stream_coach.build_word_spans_html(session)}</div>', unsafe_allow_html=True)
        if session.error:
            st.error(session.error)
        elif not session.connected:
            st.caption("Connecting to Deepgram...")
        else:
            st.caption("🔴 Live — words light up green as recognized, in real time.")
        if st.button("↺ Reset live session", key=f"reset_{session_key}"):
            session.stop()
            del st.session_state[session_key]
            st.rerun()

st.write("")

# ---------------------------------------------------------------------------
# Practice Mode — record a clip, get accurate word-by-word scoring
# ---------------------------------------------------------------------------
st.markdown('<div class="qsc-card">', unsafe_allow_html=True)
st.markdown('<span class="qsc-label">Your recitation — Practice Mode</span>', unsafe_allow_html=True)
st.caption("Record a few seconds reciting the ayah above, then check it — this is the accurate, tested path.")
audio_value = st.audio_input("Record yourself reciting the ayah above")
engine = st.radio(
    "Transcription engine", ["Whisper (local, free, no internet risk)", "Google Web Speech (lighter, needs internet)"],
    horizontal=True, label_visibility="collapsed",
)
engine_key = "whisper" if "Whisper" in engine else "google"

if audio_value is not None:
    if st.button("✅ Check my recitation", type="primary"):
        with st.spinner("Transcribing and comparing..."):
            audio_bytes = audio_value.getvalue()
            recited_text = recitation_coach.transcribe_audio(audio_bytes, engine=engine_key)
            comparison = recitation_coach.compare_recitation(reference["arabic"], recited_text)
            feedback_text = recitation_coach.generate_feedback(comparison, lang=feedback_lang)

        st.markdown("**What you recited (transcribed):**")
        st.markdown(f'<div class="arabic-text">{recited_text or "*(nothing recognized)*"}</div>', unsafe_allow_html=True)

        st.markdown("**Word-by-word feedback:**")
        html_words = ""
        for w in comparison["words"]:
            cls = {
                "correct": "qsc-word-correct",
                "wrong": "qsc-word-wrong",
                "missing": "qsc-word-missing",
                "extra": "qsc-word-wrong",
            }[w["status"]]
            label = w["text"] if w["status"] != "missing" else f"({w['text']})"
            html_words += f'<span class="qsc-word {cls}">{label}</span>'
        st.markdown(html_words, unsafe_allow_html=True)

        st.progress(comparison["accuracy"] / 100, text=f"Accuracy: {comparison['accuracy']}%")
        st.markdown(f"**Coach feedback:** {feedback_text}")

        audio_feedback = tts.speak(feedback_text, lang=feedback_lang)
        if audio_feedback:
            st.audio(audio_feedback, format="audio/mp3")

        db.log_recitation_session(surah_number, ayah_number, comparison["accuracy"])
        if comparison["accuracy"] >= 90:
            db.add_goal(
                "recitation_practice",
                f"Recited {surah_choice.split('(')[0].strip()} {ayah_number} accurately",
                DAILY_GOAL_POINTS["recitation_practice"],
            )
            db.toggle_goal(db.get_goals_for_date()[-1]["id"], True)
            st.success("🎉 Great job! Logged as a completed goal for today.")

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Recent sessions
# ---------------------------------------------------------------------------
history = db.get_recitation_history(limit=10)
if history:
    st.markdown('<div class="qsc-card qsc-card-tight">', unsafe_allow_html=True)
    st.markdown('<span class="qsc-label">Recent practice sessions</span>', unsafe_allow_html=True)
    for h in history:
        st.markdown(f"- Surah {h['surah']}:{h['ayah']} — **{h['accuracy']}%** accuracy ({h['created_at'][:16].replace('T',' ')})")
    st.markdown("</div>", unsafe_allow_html=True)
