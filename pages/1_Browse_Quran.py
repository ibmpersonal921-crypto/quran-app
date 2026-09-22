import sys
from pathlib import Path

# --- Make sure the project root is importable no matter how Streamlit
#     resolves this page's working directory (belt-and-suspenders fix for
#     "ModuleNotFoundError: No module named 'utils'" style deploy issues) ---
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from config import APP_NAME, DAILY_GOAL_POINTS
from utils.helpers import inject_css, page_header, render_sidebar_branding, render_sidebar_settings
from database import db
from services import quran_api

db.init_db()
inject_css()

with st.sidebar:
    render_sidebar_branding()
settings = render_sidebar_settings()

page_header("Browse Quran", "Read, listen, and follow along — every surah, every reciter.", "📖")

# ---------------------------------------------------------------------------
# Search (kept separate from the main browse flow)
# ---------------------------------------------------------------------------
keyword = st.text_input("🔍 Search the Quran (by translation keyword)", placeholder="e.g. patience, mercy, forgiveness")
if keyword:
    with st.spinner("Searching..."):
        matches = quran_api.search_quran(keyword, edition=settings["translation_edition"])
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
# Surah picker
# ---------------------------------------------------------------------------
surahs = quran_api.get_surah_list()
if not surahs:
    st.error("Couldn't load the surah list — check your internet connection and reload the page.")
    st.stop()

surah_labels = [f"{s['number']}. {s['englishName']} — {s['englishNameTranslation']}" for s in surahs]
surah_choice = st.selectbox("Surah", surah_labels, index=0, label_visibility="collapsed")
surah_number = int(surah_choice.split(".")[0])
surah_row = next(s for s in surahs if s["number"] == surah_number)
ayah_count = surah_row["numberOfAyahs"]

# Range slider — defaults to a manageable window (1-10) for long surahs,
# full range for short ones, just like the reference UI.
default_end = min(10, ayah_count) if ayah_count > 15 else ayah_count
range_key = f"range_{surah_number}"
if range_key not in st.session_state:
    st.session_state[range_key] = (1, default_end)
start_ayah, end_ayah = st.slider(
    "Ayah range", min_value=1, max_value=ayah_count, key=range_key
)

with st.spinner("Loading surah text..."):
    full = quran_api.get_surah_full_multilang(surah_number, settings["translation_edition"])

if not full:
    st.error("Couldn't load this surah's text right now.")
    st.stop()

meta = full["meta"]
st.markdown(
    f"""
    <div style="display:flex;justify-content:space-between;align-items:baseline;margin:6px 0 18px 0;">
        <span class="qsc-label">{meta.get('revelationType')} · {meta.get('numberOfAyahs')} verses</span>
        <span class="arabic-text" style="font-size:1.4rem;color:var(--gold,#d4af37);">{meta.get('name')}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Full-surah reference player (reciter chosen in sidebar Settings)
# ---------------------------------------------------------------------------
st.markdown('<div class="qsc-card qsc-card-tight">', unsafe_allow_html=True)
st.markdown(f'<span class="qsc-label">Full surah — {settings["reciter_name"]}</span>', unsafe_allow_html=True)
st.audio(quran_api.get_surah_audio_url(surah_number, settings["reciter_id"]), format="audio/mp3")
st.caption("Streamed from the Al Quran Cloud CDN — nothing stored locally.")
st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Ayah-by-ayah, sliced to the selected range
# ---------------------------------------------------------------------------
st.markdown('<div class="qsc-card">', unsafe_allow_html=True)
lo, hi = start_ayah - 1, end_ayah  # zero-indexed slice bounds

for idx in range(lo, hi):
    arabic_ayah = full["arabic"][idx]
    translation_ayah = full["translation"][idx] if idx < len(full["translation"]) else {}
    translit_ayah = full["transliteration"][idx] if idx < len(full["transliteration"]) else {}
    n = arabic_ayah["numberInSurah"]

    st.markdown('<hr class="qsc-divider"/>', unsafe_allow_html=True)
    badge_col, text_col, action_col = st.columns([0.6, 6, 1])
    with badge_col:
        st.markdown(f'<div class="qsc-ayah-badge">{n}</div>', unsafe_allow_html=True)
    with text_col:
        st.markdown(
            f'<div class="arabic-text" style="font-size:{settings["arabic_size"]}px;">{arabic_ayah["text"]}</div>',
            unsafe_allow_html=True,
        )
        if settings["show_translit"] and translit_ayah.get("text"):
            st.markdown(
                f'<p style="color:#b9c9c0;font-style:italic;margin:6px 0;">{translit_ayah["text"]}</p>',
                unsafe_allow_html=True,
            )
        st.markdown(f'<p style="color:#f4f7f5;">{translation_ayah.get("text","")}</p>', unsafe_allow_html=True)
        st.audio(quran_api.get_ayah_audio_url(arabic_ayah["number"], settings["reciter_id"]), format="audio/mp3")
    with action_col:
        if st.button("➕ Goal", key=f"goal_{surah_number}_{n}"):
            db.add_goal(
                "read_verse",
                f"Learn {meta.get('englishName')} {surah_number}:{n}",
                DAILY_GOAL_POINTS["read_verse"],
            )
            st.toast("Added to today's goals!")

st.markdown("</div>", unsafe_allow_html=True)
