import streamlit as st

from config import APP_NAME, APP_ICON, RECITERS, DEFAULT_RECITER, TRANSLATION_EDITIONS, DAILY_GOAL_POINTS
from utils.helpers import inject_css, page_header
from database import db
from services import quran_api

st.set_page_config(page_title=f"{APP_NAME} — Browse Quran", page_icon="📖", layout="wide")
db.init_db()
inject_css()

page_header("Browse Quran", "Read, listen, and follow along — every surah, every reciter.", "📖")

# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------
surahs = quran_api.get_surah_list()
if not surahs:
    st.error("Couldn't load the surah list — check your internet connection and reload the page.")
    st.stop()

c1, c2, c3 = st.columns([2, 1.5, 1.5])
with c1:
    surah_labels = [f"{s['number']}. {s['englishName']} ({s['name']})" for s in surahs]
    surah_choice = st.selectbox("Surah", surah_labels, index=0)
    surah_number = int(surah_choice.split(".")[0])
with c2:
    translation_choice = st.selectbox(
        "Translation", list(TRANSLATION_EDITIONS.values()), index=0
    )
    translation_edition = [k for k, v in TRANSLATION_EDITIONS.items() if v == translation_choice][0]
with c3:
    reciter_choice = st.selectbox("Reciter", list(RECITERS.keys()), index=0)
    reciter_id = RECITERS[reciter_choice]

search_col, _ = st.columns([3, 2])
with search_col:
    keyword = st.text_input("🔍 Search the Quran (by translation keyword)", placeholder="e.g. patience, mercy, forgiveness")

if keyword:
    with st.spinner("Searching..."):
        matches = quran_api.search_quran(keyword, edition=translation_edition)
    st.markdown(f'<div class="qsc-card"><span class="qsc-label">Results for "{keyword}"</span>', unsafe_allow_html=True)
    if not matches:
        st.caption("No matches found.")
    for m in matches[:15]:
        s_no = m.get("surah", {}).get("number")
        a_no = m.get("numberInSurah")
        st.markdown(f"**{m.get('surah',{}).get('englishName')} {s_no}:{a_no}** — {m.get('text')}")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ---------------------------------------------------------------------------
# Full surah audio player
# ---------------------------------------------------------------------------
st.markdown('<div class="qsc-card qsc-card-tight">', unsafe_allow_html=True)
st.markdown(f'<span class="qsc-label">Full surah recitation — {reciter_choice}</span>', unsafe_allow_html=True)
surah_audio_url = quran_api.get_surah_audio_url(surah_number, reciter_id)
st.audio(surah_audio_url, format="audio/mp3")
st.caption("Pre-recorded recitations streamed from the Al Quran Cloud CDN (islamic.network) — no local storage needed.")
st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Ayah-by-ayah view
# ---------------------------------------------------------------------------
with st.spinner("Loading surah text..."):
    bilingual = quran_api.get_surah_bilingual(surah_number, translation_edition)

if not bilingual:
    st.error("Couldn't load this surah's text right now.")
    st.stop()

meta = bilingual["surah_meta"]
st.markdown(
    f"""
    <div class="qsc-card">
        <div class="qsc-card-header">
            <span class="qsc-tag">{meta.get('englishName')} · {meta.get('englishNameTranslation')}</span>
            <span class="qsc-label">{meta.get('revelationType')} · {meta.get('numberOfAyahs')} ayahs</span>
        </div>
    """,
    unsafe_allow_html=True,
)

for arabic_ayah, translation_ayah in zip(bilingual["arabic"], bilingual["translation"]):
    n = arabic_ayah["numberInSurah"]
    st.markdown('<hr class="qsc-divider"/>', unsafe_allow_html=True)
    top_c1, top_c2 = st.columns([1, 6])
    with top_c1:
        st.markdown(f'<span class="qsc-tag">Ayah {n}</span>', unsafe_allow_html=True)
        audio_url = quran_api.get_ayah_audio_url(arabic_ayah["number"], reciter_id)
        st.audio(audio_url, format="audio/mp3")
        if st.button("➕ Goal", key=f"goal_{surah_number}_{n}"):
            db.add_goal(
                "read_verse",
                f"Learn {meta.get('englishName')} {surah_number}:{n}",
                DAILY_GOAL_POINTS["read_verse"],
            )
            st.toast("Added to today's goals!")
    with top_c2:
        st.markdown(f'<div class="arabic-text" style="font-size:1.6rem;">{arabic_ayah["text"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<p style="color:#f4f7f5;">{translation_ayah["text"]}</p>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
