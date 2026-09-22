"""
services/tts.py
----------------
Free text-to-speech via gTTS (uses Google Translate's public TTS endpoint —
no API key, but it does need an internet connection). Used for:
  - Reading recitation-coach feedback aloud (Arabic / Urdu / English)
  - Optional "listen" button on AI Companion answers

If you later want offline / higher-quality voices, swap this module for
Coqui TTS or piper-tts (both free & open-source, run fully locally) without
touching any calling code — every caller only sees `speak(text, lang)`.
"""

import io

import streamlit as st
from gtts import gTTS


@st.cache_data(ttl=60 * 60, show_spinner=False)
def speak(text: str, lang: str = "ar") -> bytes:
    """
    lang: 'ar' (Arabic), 'ur' (Urdu), or 'en' (English).
    Returns raw mp3 bytes suitable for st.audio(...).
    """
    if not text.strip():
        return b""
    try:
        buf = io.BytesIO()
        gTTS(text=text, lang=lang).write_to_fp(buf)
        return buf.getvalue()
    except Exception:
        return b""
