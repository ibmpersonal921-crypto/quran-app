import streamlit as st

from config import APP_NAME, FEEDBACK_LANGUAGES
from utils.helpers import inject_css, page_header
from database import db
from services import quran_api, recitation_coach, tts

st.set_page_config(page_title=f"{APP_NAME} — Recitation Coach", page_icon="🎙️", layout="wide")
db.init_db()
inject_css()

page_header("Recitation Coach", "Recite an ayah, get instant word-by-word correction.", "🎙️")

st.markdown(
    """
    <div class="qsc-card qsc-card-tight" style="border-color:rgba(212,175,55,0.35);">
    🎧 <b>How this works:</b> record a short clip of yourself reciting the ayah below, then tap
    "Check my recitation". You'll get colour-coded feedback in 1–3 seconds — correct words in
    green, mistakes in red, skipped words in gold — plus a spoken tip. It's a tight loop, not a
    continuous phone call, but works great for repeated practice. See the README for how to
    extend this into a true streaming live-call experience.
    </div>
    """,
    unsafe_allow_html=True,
)

surahs = quran_api.get_surah_list()
if not surahs:
    st.error("Couldn't load the surah list — check your internet connection and reload.")
    st.stop()

c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    surah_labels = [f"{s['number']}. {s['englishName']} ({s['name']})" for s in surahs]
    surah_choice = st.selectbox("Surah to practice", surah_labels, index=109)  # default An-Nasr
    surah_number = int(surah_choice.split(".")[0])
    ayah_count = next(s["numberOfAyahs"] for s in surahs if s["number"] == surah_number)
with c2:
    ayah_number = st.number_input("Ayah #", min_value=1, max_value=ayah_count, value=1, step=1)
with c3:
    feedback_lang_label = st.selectbox("Feedback voice", list(FEEDBACK_LANGUAGES.keys()), index=2)
    feedback_lang = FEEDBACK_LANGUAGES[feedback_lang_label]

reference = quran_api.get_ayah_multilang(surah_number, ayah_number)

st.markdown('<div class="qsc-card">', unsafe_allow_html=True)
st.markdown('<span class="qsc-label">Reference text</span>', unsafe_allow_html=True)
if reference.get("arabic"):
    st.markdown(f'<div class="arabic-text" style="font-size:1.9rem;">{reference["arabic"]}</div>', unsafe_allow_html=True)
    st.caption(reference.get("transliteration", ""))
    st.write(reference.get("english", ""))
else:
    st.warning("Couldn't load this ayah.")
    st.stop()
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="qsc-card">', unsafe_allow_html=True)
st.markdown('<span class="qsc-label">Your recitation</span>', unsafe_allow_html=True)
audio_value = st.audio_input("Record yourself reciting the ayah above")

if audio_value is not None:
    if st.button("✅ Check my recitation", type="primary"):
        with st.spinner("Transcribing and comparing..."):
            audio_bytes = audio_value.getvalue()
            recited_text = recitation_coach.transcribe_audio(audio_bytes)
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
            from config import DAILY_GOAL_POINTS

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
