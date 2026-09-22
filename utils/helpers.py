"""
utils/helpers.py
-----------------
Small shared utilities used across pages: CSS injection, Arabic text
normalization (for lenient recitation comparison), shared sidebar settings,
and date/streak math.
"""

import re
import datetime as dt

import streamlit as st

from config import STYLE_CSS_PATH, RECITERS, DEFAULT_RECITER, TRANSLATION_EDITIONS, DEFAULT_TRANSLATION


def inject_css() -> None:
    """Load assets/style.css into the page. Call once at the top of every page."""
    try:
        with open(STYLE_CSS_PATH, "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("style.css not found — running with default Streamlit theme.")


def page_header(title: str, subtitle: str = "", emoji: str = "📖") -> None:
    """Consistent curved header block used on every page."""
    st.markdown(
        f"""
        <div class="qsc-header">
            <span class="emoji">{emoji}</span>
            <div>
                <h1>{title}</h1>
                <p>{subtitle}</p>
            </div>
        </div>
        <hr class="qsc-divider"/>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_branding() -> None:
    from config import APP_NAME, APP_TAGLINE, APP_ICON

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


def render_sidebar_settings() -> dict:
    """
    Inline, collapsible Settings panel living in the sidebar (matches the
    reference UI) — reciter, translation, Arabic text size, transliteration
    toggle. Values live in st.session_state, which Streamlit keeps alive
    across every page in a multipage app, so a choice made here sticks as
    you navigate. Every page should call this near the top and read its
    return value instead of building its own reciter/translation pickers.
    """
    reciter_names = list(RECITERS.keys())
    default_reciter_name = next(
        (name for name, edition in RECITERS.items() if edition == DEFAULT_RECITER), reciter_names[0]
    )
    translation_labels = list(TRANSLATION_EDITIONS.values())
    default_translation_label = TRANSLATION_EDITIONS.get(DEFAULT_TRANSLATION, translation_labels[0])

    with st.sidebar.expander("⚙️ Settings", expanded=False):
        reciter_name = st.selectbox(
            "Reciter", reciter_names,
            index=reciter_names.index(st.session_state.get("settings_reciter", default_reciter_name))
            if st.session_state.get("settings_reciter", default_reciter_name) in reciter_names else 0,
            key="settings_reciter",
        )
        translation_label = st.selectbox(
            "Translation", translation_labels,
            index=translation_labels.index(st.session_state.get("settings_translation", default_translation_label))
            if st.session_state.get("settings_translation", default_translation_label) in translation_labels else 0,
            key="settings_translation",
        )
        st.slider("Arabic size", 22, 48, st.session_state.get("settings_arabic_size", 28), key="settings_arabic_size")
        st.toggle(
            "Show transliteration",
            value=st.session_state.get("settings_show_translit", True),
            key="settings_show_translit",
        )

    translation_edition = next(
        (code for code, label in TRANSLATION_EDITIONS.items() if label == translation_label),
        DEFAULT_TRANSLATION,
    )
    return {
        "reciter_name": reciter_name,
        "reciter_id": RECITERS[reciter_name],
        "translation_label": translation_label,
        "translation_edition": translation_edition,
        "arabic_size": st.session_state.get("settings_arabic_size", 28),
        "show_translit": st.session_state.get("settings_show_translit", True),
    }


# ---------------------------------------------------------------------------
# Arabic text normalization — used to lenient-compare recited text against
# the reference ayah (strip diacritics/tashkeel so minor tajweed marks don't
# register as "wrong word", while still catching real word-level mistakes).
# ---------------------------------------------------------------------------
_ARABIC_DIACRITICS = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED\u08D4-\u08E1\u08E3-\u08FF]"
)
_TATWEEL = "\u0640"


def normalize_arabic(text: str) -> str:
    """Strip diacritics/tatweel and normalize alef/ya/ta-marbuta variants."""
    if not text:
        return ""
    text = _ARABIC_DIACRITICS.sub("", text)
    text = text.replace(_TATWEEL, "")
    text = re.sub(r"[إأآا]", "ا", text)
    text = text.replace("ى", "ي").replace("ة", "ه")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def strip_diacritics_only(text: str) -> str:
    """Strip diacritics but keep letter variants — used for display diffing."""
    if not text:
        return ""
    text = _ARABIC_DIACRITICS.sub("", text)
    return text.replace(_TATWEEL, "")


# ---------------------------------------------------------------------------
# Date / streak helpers
# ---------------------------------------------------------------------------
def today_str() -> str:
    return dt.date.today().isoformat()


def day_of_year() -> int:
    return dt.date.today().timetuple().tm_yday


def compute_streak(completed_dates: list) -> int:
    """
    completed_dates: list of 'YYYY-MM-DD' strings where at least one goal
    was completed. Returns the current consecutive-day streak ending today
    (or yesterday, so the streak doesn't reset the instant midnight passes).
    """
    if not completed_dates:
        return 0
    dates = sorted({dt.date.fromisoformat(d) for d in completed_dates}, reverse=True)
    today = dt.date.today()
    streak = 0
    cursor = today
    date_set = set(dates)
    # allow the streak to still "count" if today hasn't been done yet but
    # yesterday was (so the user doesn't see it snap to 0 first thing AM)
    if today not in date_set:
        cursor = today - dt.timedelta(days=1)
        if cursor not in date_set:
            return 0
    while cursor in date_set:
        streak += 1
        cursor -= dt.timedelta(days=1)
    return streak
