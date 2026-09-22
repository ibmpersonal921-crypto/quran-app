"""
services/quran_api.py
----------------------
Thin, cached wrapper around the free, unauthenticated Al Quran Cloud API
(https://alquran.cloud/api) and its media CDN (https://alquran.cloud/cdn).

Every function degrades gracefully (returns None / [] and lets the caller
show a friendly message) instead of crashing the app if the network call
fails — important since this app has no fallback local copy of the Quran.
"""

import requests
import streamlit as st

from config import (
    QURAN_API_BASE,
    QURAN_CDN_BASE,
    ARABIC_EDITION,
    DEFAULT_TRANSLATION,
    VERSE_OF_DAY_POOL,
)

TIMEOUT = 10


def _get(url: str, params: dict = None):
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if data.get("code") == 200:
            return data.get("data")
        return None
    except requests.RequestException:
        return None


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def get_surah_list() -> list:
    """All 114 surahs with number, name, English name, ayah count, revelation type."""
    data = _get(f"{QURAN_API_BASE}/surah")
    return data or []


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def get_surah_text(surah_number: int, edition: str = ARABIC_EDITION) -> dict:
    """Full surah text for one edition (Arabic script or a translation)."""
    return _get(f"{QURAN_API_BASE}/surah/{surah_number}/{edition}")


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def get_surah_bilingual(surah_number: int, translation_edition: str = DEFAULT_TRANSLATION) -> dict:
    """
    Returns {"arabic": [...ayahs...], "translation": [...ayahs...]} aligned
    by index, so the UI can show them side by side.
    """
    arabic = get_surah_text(surah_number, ARABIC_EDITION)
    translation = get_surah_text(surah_number, translation_edition)
    if not arabic or not translation:
        return {}
    return {
        "surah_meta": {k: v for k, v in arabic.items() if k != "ayahs"},
        "arabic": arabic.get("ayahs", []),
        "translation": translation.get("ayahs", []),
    }


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def get_ayah(surah_number: int, ayah_number: int, edition: str = ARABIC_EDITION) -> dict:
    """Single ayah, referenced as 'surah:ayah' (e.g. '2:255')."""
    return _get(f"{QURAN_API_BASE}/ayah/{surah_number}:{ayah_number}/{edition}")


@st.cache_data(ttl=60 * 60 * 6, show_spinner=False)
def search_quran(keyword: str, edition: str = DEFAULT_TRANSLATION, surah: str = "all") -> list:
    """Keyword search across the Quran translation text. Returns list of matches."""
    if not keyword.strip():
        return []
    data = _get(f"{QURAN_API_BASE}/search/{keyword}/{surah}/{edition}")
    if not data:
        return []
    return data.get("matches", [])


def get_ayah_audio_url(global_ayah_number: int, reciter: str = "ar.alafasy", bitrate: int = 128) -> str:
    """
    Direct CDN mp3 for a single ayah. global_ayah_number is the ayah's
    position across the whole Quran (1-6236) — every ayah object returned
    by the API includes this as `number`.
    """
    return f"{QURAN_CDN_BASE}/audio/{bitrate}/{reciter}/{global_ayah_number}.mp3"


def get_surah_audio_url(surah_number: int, reciter: str = "ar.alafasy", bitrate: int = 128) -> str:
    """Direct CDN mp3 for a full surah recitation."""
    return f"{QURAN_CDN_BASE}/audio-surah/{bitrate}/{reciter}/{surah_number}.mp3"


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def get_ayah_multilang(surah_number: int, ayah_number: int) -> dict:
    """Arabic + English + Urdu text for one ayah — used by the AI chatbot
    to ground answers and by the dashboard's Verse of the Day card."""
    arabic = get_ayah(surah_number, ayah_number, ARABIC_EDITION)
    english = get_ayah(surah_number, ayah_number, DEFAULT_TRANSLATION)
    urdu = get_ayah(surah_number, ayah_number, "ur.jalandhry")
    transliteration = get_ayah(surah_number, ayah_number, "en.transliteration")
    return {
        "arabic": arabic.get("text") if arabic else None,
        "english": english.get("text") if english else None,
        "urdu": urdu.get("text") if urdu else None,
        "transliteration": transliteration.get("text") if transliteration else None,
        "global_ayah_number": arabic.get("number") if arabic else None,
    }


def get_verse_range_multilang(surah_number: int, start_ayah: int, end_ayah: int) -> dict:
    """Fetch and concatenate a small range of ayahs (used for Verse of the Day
    and for 'add a verse range as a daily goal')."""
    arabic_parts, english_parts, urdu_parts, translit_parts = [], [], [], []
    first_global_number = None
    for n in range(start_ayah, end_ayah + 1):
        data = get_ayah_multilang(surah_number, n)
        if first_global_number is None:
            first_global_number = data.get("global_ayah_number")
        if data.get("arabic"):
            arabic_parts.append(f"{data['arabic']} \u06dd{_to_arabic_numeral(n)}")
        if data.get("english"):
            english_parts.append(data["english"])
        if data.get("urdu"):
            urdu_parts.append(data["urdu"])
        if data.get("transliteration"):
            translit_parts.append(data["transliteration"])
    return {
        "arabic": " ".join(arabic_parts),
        "english": " ".join(english_parts),
        "urdu": " ".join(urdu_parts),
        "transliteration": " ".join(translit_parts),
        "global_ayah_number": first_global_number,
    }


def _to_arabic_numeral(n: int) -> str:
    digits = "٠١٢٣٤٥٦٧٨٩"
    return "".join(digits[int(d)] for d in str(n))


def get_verse_of_the_day() -> dict:
    """Deterministic pick from VERSE_OF_DAY_POOL based on day-of-year."""
    import datetime as _dt

    idx = _dt.date.today().timetuple().tm_yday % len(VERSE_OF_DAY_POOL)
    surah_no, start_ayah, end_ayah, label = VERSE_OF_DAY_POOL[idx]
    verse = get_verse_range_multilang(surah_no, start_ayah, end_ayah)
    verse.update(
        {
            "surah_number": surah_no,
            "start_ayah": start_ayah,
            "end_ayah": end_ayah,
            "label": label,
        }
    )
    return verse
def get_surah_full_multilang(surah_number: int, translation_edition: str):
    """
    Fetch a full surah in three editions at once (Arabic/Uthmani text,
    the user's chosen translation, and transliteration), using Al Quran
    Cloud's multi-edition endpoint:
      GET /v1/surah/{surah}/editions/{ed1},{ed2},{ed3}

    Returns a dict shaped like:
        {
            "meta": {...},                # surah-level info
            "arabic": [ {...}, ... ],      # list of ayah dicts (Uthmani)
            "translation": [ {...}, ... ], # list of ayah dicts (chosen translation)
            "transliteration": [ {...}, ... ],
        }
    or {} on failure.
    """
    editions = f"{ARABIC_EDITION},{translation_edition},{DEFAULT_TRANSLITERATION}"
    url = f"{QURAN_API_BASE}/surah/{surah_number}/editions/{editions}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        if len(data) < 3:
            return {}

        arabic_ed, translation_ed, translit_ed = data[0], data[1], data[2]

        meta = {
            "name": arabic_ed.get("name"),
            "englishName": arabic_ed.get("englishName"),
            "englishNameTranslation": arabic_ed.get("englishNameTranslation"),
            "revelationType": arabic_ed.get("revelationType"),
            "numberOfAyahs": arabic_ed.get("numberOfAyahs", len(arabic_ed.get("ayahs", []))),
        }

        return {
            "meta": meta,
            "arabic": arabic_ed.get("ayahs", []),
            "translation": translation_ed.get("ayahs", []),
            "transliteration": translit_ed.get("ayahs", []),
        }
    except Exception:
        return {}
