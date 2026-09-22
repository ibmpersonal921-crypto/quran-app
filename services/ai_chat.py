"""
services/ai_chat.py
--------------------
The "AI Companion" brain.

Why this file matters for accuracy
-----------------------------------
LLMs can hallucinate verse/hadith wording, especially under a "sound
confident" incentive. So instead of just asking Claude the raw question,
this module:

  1. Scans the question for a Quran reference ("2:255", "Surah Yasin 5")
     or a hadith reference ("Sahih Bukhari 1") using regex + the live
     surah list.
  2. If found, fetches the REAL text from the Al Quran Cloud / Hadith APIs
     (services/quran_api.py, services/hadith_api.py) and hands that to
     Claude as verified context.
  3. The system prompt instructs Claude to quote scripture ONLY from that
     verified context, to say "I can't verify that exact reference" rather
     than invent wording when nothing was retrieved, and to flag fiqh
     (jurisprudence) questions as having scholarly differences rather than
     stating one opinion as universal fact.

This is "RAG-lite" — good enough to stop the model from freely fabricating
verse text, but it is not a substitute for a qualified scholar, and the
UI/system prompt says so.
"""

import re

import streamlit as st

from config import ANTHROPIC_API_KEY, CHAT_MODEL, CHAT_MAX_TOKENS, HADITH_COLLECTIONS
from services import quran_api, hadith_api

SYSTEM_PROMPT = """You are the AI Companion inside "Quran Study Companion", a study app.
Your job is to help the user understand the Qur'an and authentic Hadith accurately.

Hard rules:
1. Only quote Qur'an or Hadith WORDING if it appears in the "VERIFIED SOURCES" block
   provided in this message. If the user asks for a specific ayah or hadith that is
   NOT in VERIFIED SOURCES, say plainly that you can't verify the exact wording here
   and suggest they check it in the app's Browse Quran page or a trusted mushaf/hadith
   collection — do NOT reconstruct or guess the wording from memory.
2. For general Islamic knowledge questions (history, meanings, context) you may answer
   from what you know, but stay factual and cite the surah/ayah or hadith collection
   and number whenever you reference one, so the user can verify it themselves.
3. For fiqh (jurisprudence) questions where scholars/madhabs differ (e.g. exact prayer
   rulings, zakat calculation details, marriage/divorce/inheritance rulings), present
   the mainstream positions and note that they differ — do NOT state one school's view
   as the single correct answer, and do NOT issue a personal fatwa. Recommend the user
   consult a qualified local scholar for a binding personal ruling.
4. Be warm, respectful, and encouraging — this is a study companion, not a debate app.
5. If a question is outside Islamic knowledge entirely, answer briefly and steer back
   to how you can help with Quran/Hadith study.
"""

# ---------------------------------------------------------------------------
# Reference detection (heuristic — good enough to ground the common cases:
# "2:255", "Surah Yasin ayah 5", "Bukhari 1")
# ---------------------------------------------------------------------------
_AYAH_REF = re.compile(r"\b(\d{1,3})\s*[:.]\s*(\d{1,3})\b")
_HADITH_REF = re.compile(
    r"\b(bukhari|muslim|abu\s?dawo?ud|tirmidh[iy]|nasa'?i|ibn\s?majah)\b\D{0,12}(\d{1,4})",
    re.IGNORECASE,
)
_HADITH_NAME_MAP = {
    "bukhari": "Sahih al-Bukhari",
    "muslim": "Sahih Muslim",
    "abudawud": "Sunan Abu Dawood",
    "abudawoud": "Sunan Abu Dawood",
    "tirmidhi": "Jami at-Tirmidhi",
    "tirmidhy": "Jami at-Tirmidhi",
    "nasai": "Sunan an-Nasa'i",
    "ibnmajah": "Sunan Ibn Majah",
}


def _find_surah_by_name(text: str):
    """Best-effort: match an English surah name mentioned in free text."""
    surahs = quran_api.get_surah_list()
    text_l = text.lower()
    for s in surahs:
        name = s.get("englishName", "").lower().replace("al-", "").strip()
        if name and name in text_l:
            return s
    return None


def _build_context(user_query: str) -> str:
    """Return a VERIFIED SOURCES block (may be empty) grounding the answer."""
    sources = []

    # Direct "surah:ayah" style reference
    m = _AYAH_REF.search(user_query)
    if m:
        surah_no, ayah_no = int(m.group(1)), int(m.group(2))
        if 1 <= surah_no <= 114:
            data = quran_api.get_ayah_multilang(surah_no, ayah_no)
            if data.get("arabic"):
                sources.append(
                    f"[Qur'an {surah_no}:{ayah_no}]\n"
                    f"Arabic: {data['arabic']}\n"
                    f"English (Saheeh International): {data['english']}\n"
                    f"Urdu (Jalandhry): {data['urdu']}"
                )

    # "Surah <name>" + a trailing number, without explicit colon
    if not sources:
        surah = _find_surah_by_name(user_query)
        num_match = re.search(r"\b(?:ayah|verse|no\.?)\s*(\d{1,3})\b", user_query, re.IGNORECASE)
        if surah and num_match:
            ayah_no = int(num_match.group(1))
            data = quran_api.get_ayah_multilang(surah["number"], ayah_no)
            if data.get("arabic"):
                sources.append(
                    f"[Qur'an {surah['number']}:{ayah_no} — Surah {surah.get('englishName')}]\n"
                    f"Arabic: {data['arabic']}\n"
                    f"English (Saheeh International): {data['english']}\n"
                    f"Urdu (Jalandhry): {data['urdu']}"
                )

    # Hadith reference
    hm = _HADITH_REF.search(user_query)
    if hm:
        key = re.sub(r"[^a-z]", "", hm.group(1).lower())
        collection_label = _HADITH_NAME_MAP.get(key)
        number = int(hm.group(2))
        if collection_label:
            hadith = hadith_api.get_hadith_by_reference(collection_label, number)
            if hadith and hadith.get("text"):
                sources.append(
                    f"[{collection_label} #{number}]\n{hadith['text']}"
                )

    # Fallback: keyword search across Quran translation for topical questions
    if not sources:
        keywords = " ".join(w for w in re.findall(r"[A-Za-z]{4,}", user_query)[:4])
        if keywords:
            matches = quran_api.search_quran(keywords)[:3]
            for match in matches:
                surah_no = match.get("surah", {}).get("number")
                ayah_no = match.get("numberInSurah")
                if surah_no and ayah_no:
                    sources.append(
                        f"[Qur'an {surah_no}:{ayah_no}]\n{match.get('text')}"
                    )

    if not sources:
        return ""
    return "VERIFIED SOURCES (only quote scripture from here):\n\n" + "\n\n".join(sources)


@st.cache_resource(show_spinner=False)
def _get_client():
    import anthropic

    if not ANTHROPIC_API_KEY:
        return None
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def ask(user_query: str, chat_history: list) -> dict:
    """
    chat_history: list of {"role": "user"|"assistant", "content": str}
    Returns {"answer": str, "grounded": bool, "context_used": str}
    """
    client = _get_client()
    if client is None:
        return {
            "answer": (
                "⚠️ No Claude API key is configured yet. Add `ANTHROPIC_API_KEY` to your "
                "`.env` file (see README) to enable the AI Companion."
            ),
            "grounded": False,
            "context_used": "",
        }

    context = _build_context(user_query)
    system = SYSTEM_PROMPT
    if context:
        system += f"\n\n{context}"

    messages = [{"role": m["role"], "content": m["content"]} for m in chat_history]
    messages.append({"role": "user", "content": user_query})

    try:
        response = client.messages.create(
            model=CHAT_MODEL,
            max_tokens=CHAT_MAX_TOKENS,
            system=system,
            messages=messages,
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        return {"answer": text, "grounded": bool(context), "context_used": context}
    except Exception as e:  # noqa: BLE001 — surface any API error to the UI, don't crash
        return {
            "answer": f"⚠️ The AI Companion couldn't reach Claude: `{e}`",
            "grounded": False,
            "context_used": "",
        }
