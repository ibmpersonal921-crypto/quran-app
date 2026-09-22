"""
services/hadith_api.py
-----------------------
Wrapper around fawazahmed0's free, unauthenticated Hadith API
(https://github.com/fawazahmed0/hadith-api), served as static JSON via
jsDelivr's CDN. No API key, no rate limit.

NOTE: this API serves fixed collections by book + hadith number — it has
no full-text search endpoint. So the AI chatbot (services/ai_chat.py) only
grounds a hadith citation when the user (or Claude) references a specific
book + number; for open-ended "what does Islam say about X" questions the
model answers from general knowledge with a clear "verify with a scholar"
disclaimer rather than pretending to quote a specific hadith.
"""

import random

import requests
import streamlit as st

from config import HADITH_API_BASE, HADITH_COLLECTIONS

TIMEOUT = 10


def _get(url: str):
    try:
        r = requests.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return None


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def get_hadith(edition: str, number: int) -> dict:
    """Fetch one hadith by edition id (e.g. 'eng-bukhari') and number."""
    data = _get(f"{HADITH_API_BASE}/editions/{edition}/{number}.min.json")
    if not data:
        return {}
    hadiths = data.get("hadiths", [])
    return hadiths[0] if hadiths else {}


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def get_collection_info(edition: str) -> dict:
    """Metadata for an edition — includes last_hadithnumber, used for random pick."""
    data = _get(f"{HADITH_API_BASE}/info.min.json")
    if not data:
        return {}
    return data.get(edition, {})


def get_random_hadith(collection_label: str = "Sahih al-Bukhari", lang: str = "en") -> dict:
    eng_id, urd_id = HADITH_COLLECTIONS.get(collection_label, HADITH_COLLECTIONS["Sahih al-Bukhari"])
    edition = urd_id if lang == "ur" else eng_id
    info = get_collection_info(edition)
    last_num = info.get("metadata", {}).get("length") or 100
    number = random.randint(1, max(1, int(last_num)))
    hadith = get_hadith(edition, number)
    return {"collection": collection_label, "edition": edition, "number": number, **hadith}


def get_hadith_by_reference(collection_label: str, number: int, lang: str = "en") -> dict:
    """Look up a specific hadith the user or the AI referenced, e.g.
    'Sahih al-Bukhari #1' — used to ground chatbot answers in real text."""
    eng_id, urd_id = HADITH_COLLECTIONS.get(collection_label, (None, None))
    if not eng_id:
        return {}
    edition = urd_id if lang == "ur" else eng_id
    return get_hadith(edition, number)
