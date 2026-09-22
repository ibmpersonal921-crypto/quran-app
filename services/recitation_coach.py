"""
services/recitation_coach.py
-----------------------------
The "AI corrects my recitation" feature.

Honest scope (read this before assuming it's a phone-call-style live AI):
---------------------------------------------------------------------------
True continuous, word-by-word "live call" correction — like a human tutor
listening while you recite non-stop — needs a *streaming* speech recognizer
that returns partial results every ~200ms while you're still talking. Free,
fully-local models (what this project uses, for cost reasons) don't do that
well for Arabic/tajweed-level accuracy yet.

What's built here instead is a tight *near-real-time loop*:
    1. You record a short chunk (a few seconds — one ayah or a phrase) using
       the browser mic (st.audio_input).
    2. It's transcribed locally with faster-whisper (free, runs on CPU).
    3. The transcript is diffed word-by-word against the correct ayah text.
    4. You get instant colour-coded + spoken feedback, then record again.
Round-trip is typically 1-3 seconds on a laptop CPU — it *feels* like a
live coaching session even though it's chunk-based, not streaming audio.
See the README "Going further" section for how to upgrade this to a real
streaming pipeline if you want to push the project further.
"""

import difflib
import tempfile

import streamlit as st

from config import WHISPER_MODEL_SIZE
from utils.helpers import normalize_arabic


@st.cache_resource(show_spinner=False)
def _get_model():
    from faster_whisper import WhisperModel

    # int8 compute type keeps this usable on a plain CPU (free hosting tiers
    # included) at the cost of a little accuracy vs float16 on a GPU.
    return WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")


def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe recorded Arabic recitation. Returns raw Arabic text."""
    if not audio_bytes:
        return ""
    model = _get_model()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
        tmp.write(audio_bytes)
        tmp.flush()
        segments, _info = model.transcribe(tmp.name, language="ar", vad_filter=True)
        return " ".join(seg.text.strip() for seg in segments).strip()


def compare_recitation(reference_text: str, recited_text: str) -> dict:
    """
    Word-level diff between the correct ayah and what was actually said.
    Returns {"words": [...], "accuracy": float 0-100}.
    Each word dict: {"status": "correct"|"wrong"|"missing"|"extra", "text": str, "expected": str|None}
    """
    ref_words = normalize_arabic(reference_text).split()
    said_words = normalize_arabic(recited_text).split()

    matcher = difflib.SequenceMatcher(a=ref_words, b=said_words)
    result = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for w in ref_words[i1:i2]:
                result.append({"status": "correct", "text": w, "expected": None})
        elif tag == "replace":
            ref_chunk = ref_words[i1:i2]
            said_chunk = said_words[j1:j2]
            for idx in range(max(len(ref_chunk), len(said_chunk))):
                expected = ref_chunk[idx] if idx < len(ref_chunk) else None
                actual = said_chunk[idx] if idx < len(said_chunk) else None
                if expected and actual:
                    result.append({"status": "wrong", "text": actual, "expected": expected})
                elif expected:
                    result.append({"status": "missing", "text": expected, "expected": expected})
                elif actual:
                    result.append({"status": "extra", "text": actual, "expected": None})
        elif tag == "delete":
            for w in ref_words[i1:i2]:
                result.append({"status": "missing", "text": w, "expected": w})
        elif tag == "insert":
            for w in said_words[j1:j2]:
                result.append({"status": "extra", "text": w, "expected": None})

    total = max(1, len(ref_words))
    correct = sum(1 for w in result if w["status"] == "correct")
    accuracy = round(100 * correct / total, 1)
    return {"words": result, "accuracy": accuracy}


def generate_feedback(comparison: dict, lang: str = "en") -> str:
    """Rule-based, human-readable feedback (no extra API cost)."""
    accuracy = comparison["accuracy"]
    wrong = [w for w in comparison["words"] if w["status"] in ("wrong", "missing")]

    if lang == "ur":
        if accuracy >= 95:
            head = "ماشاءاللہ! آپ کی تلاوت بہت درست تھی۔"
        elif accuracy >= 75:
            head = "اچھی کوشش! کچھ الفاظ پر دوبارہ توجہ دیں۔"
        else:
            head = "کوئی بات نہیں، دوبارہ آہستہ آہستہ کوشش کریں۔"
        detail = "؛ ".join(
            f"'{w['expected']}' پر توجہ دیں" for w in wrong[:3] if w.get("expected")
        )
    else:
        if accuracy >= 95:
            head = "Excellent — that was very close to the correct recitation!"
        elif accuracy >= 75:
            head = "Good attempt — a couple of words need another pass."
        else:
            head = "Let's slow down and try that again, word by word."
        detail = "; ".join(
            f"check the word '{w['expected']}'" for w in wrong[:3] if w.get("expected")
        )

    if detail:
        return f"{head} {detail}."
    return head
