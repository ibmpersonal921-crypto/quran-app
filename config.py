"""
config.py
---------
Central place for every "magic value" in the app: colors, API bases,
reciter list, translation editions, and default settings.

Change things here instead of hunting through every page.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # loads ANTHROPIC_API_KEY etc. from a local .env file, if present

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "app.db"
STYLE_CSS_PATH = BASE_DIR / "assets" / "style.css"

# ---------------------------------------------------------------------------
# App identity
# ---------------------------------------------------------------------------
APP_NAME = "Quran Study Companion"
APP_TAGLINE = "Read · Listen · Reflect"
APP_ICON = "📖"

# ---------------------------------------------------------------------------
# Theme — "Celestial Minimalist": deep indigo-to-teal atmosphere, frosted
# glass surfaces, gold as the primary accent, emerald for progress/success,
# a soft dawn-pink used sparingly as a third accent.
#
# NOTE: style.css is what actually renders the app right now — it defines
# its own :root CSS variables and doesn't import this dict. This THEME
# constant mirrors style.css's values 1:1 so any Python code that wants
# the palette (e.g. to build an inline chart or an f-string style=""
# snippet) has one source to read from instead of hardcoding hex codes.
# If you ever change one, change the other to match.
# ---------------------------------------------------------------------------
THEME = {
    # Base canvas — deep, atmospheric blend from midnight indigo into
    # emerald-teal, evoking a night sky over a mosque courtyard.
    "bg_indigo": "#0A1220",
    "bg_teal": "#06231D",
    "bg_void": "#04070C",
    # Glass surfaces — semi-transparent so backdrop-filter blur reads as
    # frosted glass rather than a flat card.
    "surface_glass": "rgba(20, 34, 32, 0.55)",
    "surface_glass_soft": "rgba(16, 28, 26, 0.40)",
    "border_glass": "rgba(255, 255, 255, 0.08)",
    "border_gold": "rgba(212, 175, 55, 0.20)",
    # Accents
    "accent_gold": "#D4AF37",
    "accent_gold_glow": "rgba(212, 175, 55, 0.35)",
    "accent_green": "#2ECC71",
    "accent_dawn": "#E9AFC9",   # soft dawn-pink — use sparingly, 1-2 spots max
    # Text
    "text_primary": "#F5F7F6",
    "text_secondary": "#B9C9C0",
    "text_muted": "#7E9186",
    # Radii
    "radius_lg": "24px",
    "radius_md": "16px",
    "radius_sm": "10px",
    # Glass elevation tiers — see design-blueprint.md section 1
    "blur_sm": "12px",   # resting tier: stat pills, list rows
    "blur_md": "20px",   # raised tier: content cards
    "blur_lg": "32px",   # floating tier: Last-Read widget, audio sheet, modals
}

FONTS = {
    "arabic": "'Amiri', 'Traditional Arabic', serif",
    "urdu": "'Noto Nastaliq Urdu', serif",
    "display": "'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif",
    "body": "'Inter', 'Plus Jakarta Sans', -apple-system, sans-serif",
}

# ---------------------------------------------------------------------------
# Al Quran Cloud API — free, unauthenticated (https://alquran.cloud/api)
# ---------------------------------------------------------------------------
QURAN_API_BASE = "https://api.alquran.cloud/v1"
QURAN_CDN_BASE = "https://cdn.islamic.network/quran"

# Default text editions
ARABIC_EDITION = "quran-uthmani"          # Uthmani script, no diacritic loss
DEFAULT_TRANSLATION = "en.sahih"          # Saheeh International (English)
DEFAULT_TRANSLITERATION = "en.transliteration"

# Translations users can pick in Settings / Browse Quran
TRANSLATION_EDITIONS = {
    "en.sahih": "English — Saheeh International",
    "en.asad": "English — Muhammad Asad",
    "en.pickthall": "English — Pickthall",
    "ur.jalandhry": "Urdu — Fateh Muhammad Jalandhry",
    "ur.kanzuliman": "Urdu — Kanzul Iman (Ahmed Raza Khan)",
}

# Reciters — identifiers verified against https://alquran.cloud/cdn
# name shown in UI -> Al Quran Cloud audio edition identifier
RECITERS = {
    "Mishary Rashid Alafasy": "ar.alafasy",
    "Abdul Basit (Murattal)": "ar.abdulbasit",
    "Abdul Basit (Mujawwad)": "ar.abdulbasitmujawwad",
    "Mahmoud Khalil Al-Husary": "ar.husary",
    "Mohamed Siddiq Al-Minshawi": "ar.minshawi",
    "Abdul Rahman Al-Sudais": "ar.sudais",
    "Saud Al-Shuraim": "ar.shuraim",
    "Ahmed Al-Ajamy": "ar.ajamy",
    "Ali Al-Hudhaify": "ar.hudhaify",
}
DEFAULT_RECITER = "ar.alafasy"
DEFAULT_BITRATE = 128  # one of 32,40,48,64,128,192 (availability varies per reciter)

# ---------------------------------------------------------------------------
# Hadith API — fawazahmed0/hadith-api, free, no auth, served via jsDelivr CDN
# https://github.com/fawazahmed0/hadith-api
# ---------------------------------------------------------------------------
HADITH_API_BASE = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1"

# collection label -> (english edition id, urdu edition id)
HADITH_COLLECTIONS = {
    "Sahih al-Bukhari": ("eng-bukhari", "urd-bukhari"),
    "Sahih Muslim": ("eng-muslim", "urd-muslim"),
    "Sunan Abu Dawood": ("eng-abudawud", "urd-abudawud"),
    "Jami at-Tirmidhi": ("eng-tirmidhi", "urd-tirmidhi"),
    "Sunan an-Nasa'i": ("eng-nasai", "urd-nasai"),
    "Sunan Ibn Majah": ("eng-ibnmajah", "urd-ibnmajah"),
}

# ---------------------------------------------------------------------------
# AI chatbot — Gemini (free tier, default) or Claude (paid, if you add credits)
# ---------------------------------------------------------------------------
def _resolve_key(name: str) -> str:
    """Check os.environ (.env locally, or Streamlit Cloud root-level secrets —
    those are exposed as env vars automatically) and st.secrets directly."""
    key = os.getenv(name, "")
    if key:
        return key
    try:
        import streamlit as st

        return st.secrets.get(name, "")
    except Exception:
        return ""


# "gemini" (default — free tier, no card needed) or "anthropic" (paid, if you
# add credits at console.anthropic.com). Flip with the AI_PROVIDER env var —
# no code changes needed either way.
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()

GEMINI_API_KEY = _resolve_key("GEMINI_API_KEY")
# "gemini-flash-latest" is an alias Google repoints at their current best
# Flash model — safer than hardcoding a version that gets deprecated.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

ANTHROPIC_API_KEY = _resolve_key("ANTHROPIC_API_KEY")
# Haiku 4.5 is the cheapest current Claude model — only used if
# AI_PROVIDER=anthropic and you've added credits.
CHAT_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
CHAT_MAX_TOKENS = 2048

# ---------------------------------------------------------------------------
# Recitation coach
# ---------------------------------------------------------------------------
# Local, free speech-to-text via faster-whisper. "tiny"/"base" run on CPU
# fine; "small" is more accurate but slower. See services/recitation_coach.py
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")
FEEDBACK_LANGUAGES = {"Arabic": "ar", "Urdu": "ur", "English": "en"}

# ---------------------------------------------------------------------------
# Verse of the Day — a curated rotation of short, meaningful passages.
# Picked deterministically by day-of-year so everyone sees the same verse on
# a given date (and it repeats every ~30 days rather than needing a huge list).
# Format: (surah_number, start_ayah, end_ayah, short_label)
# ---------------------------------------------------------------------------
VERSE_OF_DAY_POOL = [
    (110, 1, 3, "Surah An-Nasr, 1–3"),
    (94, 1, 8, "Surah Ash-Sharh, 1–8"),
    (103, 1, 3, "Surah Al-Asr, 1–3"),
    (112, 1, 4, "Surah Al-Ikhlas, 1–4"),
    (2, 286, 286, "Surah Al-Baqarah, 286"),
    (2, 255, 255, "Ayat al-Kursi, 2:255"),
    (94, 5, 6, "Surah Ash-Sharh, 5–6"),
    (13, 28, 28, "Surah Ar-Ra'd, 28"),
    (65, 2, 3, "Surah At-Talaq, 2–3"),
    (3, 159, 159, "Surah Aal-e-Imran, 159"),
    (49, 13, 13, "Surah Al-Hujurat, 13"),
    (17, 23, 24, "Surah Al-Isra, 23–24"),
    (31, 17, 17, "Surah Luqman, 17"),
    (39, 53, 53, "Surah Az-Zumar, 53"),
    (55, 1, 4, "Surah Ar-Rahman, 1–4"),
    (7, 199, 199, "Surah Al-A'raf, 199"),
    (16, 90, 90, "Surah An-Nahl, 90"),
    (24, 35, 35, "Surah An-Nur, 35"),
    (2, 152, 152, "Surah Al-Baqarah, 152"),
    (29, 45, 45, "Surah Al-Ankabut, 45"),
]

# ---------------------------------------------------------------------------
# Daily goals
# ---------------------------------------------------------------------------
DAILY_GOAL_POINTS = {
    "memorize_verse": 10,
    "read_verse": 5,
    "listen_recitation": 3,
    "recitation_practice": 8,
    "custom": 5,
}
