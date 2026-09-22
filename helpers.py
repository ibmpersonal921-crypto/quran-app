"""
utils/helpers.py
-----------------
Small shared utilities used across pages: CSS injection, Arabic text
normalization (for lenient recitation comparison), and date/streak math.
"""

import re
import datetime as dt

import streamlit as st

from config import STYLE_CSS_PATH, THEME


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
