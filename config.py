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
# Theme — emerald green, fading/gradient, curved cards
# Used by assets/style.css via Streamlit's markdown injection.
# ---------------------------------------------------------------------------
THEME = {
    "bg_start": "#04120c",       # near-black emerald (top of gradient)
    "bg_end": "#0b2e22",         # deep emerald (bottom of gradient)
    "surface": "#0f2c22",        # card background
    "surface_soft": "#123527",   # secondary card background
    "border": "rgba(212, 175, 55, 0.18)",  # faint gold hairline
    "accent_gold": "#d4af37",    # gold accent (surah tag, highlights)
    "accent_green": "#2ecc71",   # bright emerald accent (buttons, success)
    "text_primary": "#f4f7f5",
    "text_secondary": "#b9c9c0",
    "text_muted": "#7e9186",
    "radius_lg": "22px",
    "radius_md": "16px",
    "radius_sm": "10px",
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
# AI chatbot (Claude API)
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
# Haiku 4.5 is the cheapest current model with near-frontier quality — good
# default for a student project. Swap to "claude-sonnet-5" for higher quality
# at higher cost. See README for how to get a key / free trial credit.
CHAT_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
CHAT_MAX_TOKENS = 1000

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
