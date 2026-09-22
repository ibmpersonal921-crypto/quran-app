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

    return WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")


def transcribe_audio(audio_bytes: bytes, engine: str = "whisper") -> str:
    """
    Transcribe recorded Arabic recitation. Two engines:
    - "whisper" (default): faster-whisper, fully local/free, no internet
      needed per-request, but downloads a model on first run — can be slow
      on constrained free hosting.
    - "google": free, keyless Google Web Speech API via SpeechRecognition —
      no model download, lighter on constrained free hosting, but needs
      internet per request and is an unofficial/rate-limited endpoint.
    Both read st.audio_input's bytes directly — Streamlit encodes that as
    real WAV, so no ffmpeg/pydub conversion step is needed either way.
    """
    if not audio_bytes:
        return ""
    if engine == "google":
        import io as _io
        import speech_recognition as sr

        recognizer = sr.Recognizer()
        with sr.AudioFile(_io.BytesIO(audio_bytes)) as source:
            data = recognizer.record(source)
        try:
            return recognizer.recognize_google(data, language="ar-SA")
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            raise RuntimeError(f"Google Web Speech error: {e}") from e

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


# ---------------------------------------------------------------------------
# "Live Mode" (experimental) — continuous browser speech recognition
# ---------------------------------------------------------------------------
# This is the honest attempt at the "live phone-call" experience: it uses
# the browser's FREE, built-in Web Speech API (Chrome/Edge — it's not
# available in Safari or Firefox) to listen continuously and light up words
# green/red AS you recite, with no per-chunk delay.
#
# Two real caveats, on purpose stated plainly rather than hidden:
#  1. Browser support: Chrome or Edge only (desktop or Android). No iOS
#     Safari, no Firefox. The component detects this and says so instead of
#     silently doing nothing.
#  2. Recognition quality: this uses the browser's general-purpose Arabic
#     speech model, not one trained on tajweed-precise Quranic recitation —
#     so it's a good "does this roughly flow correctly, live" signal, not a
#     tajweed-grade judge. Practice Mode above (faster-whisper) remains the
#     more accurate, fully-tested option; treat Live Mode as a bonus.
def build_live_mode_html(reference_arabic: str, lang_code: str = "ar-SA", feedback_lang: str = "en-US") -> str:
    """
    Live Voice Call — 100% free, runs entirely in the browser.

    Uses the Web Speech API twice:
      - SpeechRecognition (STT) to hear the reciter, continuously, live.
      - speechSynthesis (TTS) to talk back — a short spoken cue the moment a
        word is matched or missed, plus a spoken wrap-up when the ayah ends —
        so it feels like a live call with a coach rather than a silent
        transcript. No API key, no server, no cost: both APIs ship in the
        browser (Chrome/Edge; Web Speech needs an internet connection to
        Google's recognition service under the hood, but there's no key to
        manage and nothing to pay for).
    """
    import json

    ref_json = json.dumps(reference_arabic)
    lang_json = json.dumps(lang_code)
    feedback_lang_json = json.dumps(feedback_lang)

    return f"""
<div id="qsc-live-root" style="font-family:'Poppins',sans-serif;color:#f4f7f5;background:linear-gradient(160deg,#0f2c22,#123527);border:1px solid rgba(212,175,55,0.18);border-radius:22px;padding:22px 24px;">
  <style>
    #qsc-live-root .ref {{ font-family:'Amiri','Traditional Arabic',serif; direction:rtl; text-align:right; line-height:2.6; font-size:1.7rem; }}
    #qsc-live-root .w {{ display:inline-block; margin:3px 5px; padding:3px 9px; border-radius:999px; transition: all .15s ease; }}
    #qsc-live-root .pending {{ color:#b9c9c0; }}
    #qsc-live-root .correct {{ background:rgba(46,204,113,0.15); color:#7CE8A6; border:1px solid rgba(46,204,113,0.35); }}
    #qsc-live-root .wrong {{ background:rgba(231,76,60,0.15); color:#ff8f80; border:1px solid rgba(231,76,60,0.35); }}
    #qsc-live-root button {{ background:linear-gradient(135deg,#1f7a4d,#14512f); color:#f4f7f5; border:1px solid rgba(212,175,55,0.25); border-radius:999px; padding:0.5em 1.3em; font-weight:500; cursor:pointer; margin-right:8px; }}
    #qsc-live-root button:disabled {{ opacity:0.5; cursor:not-allowed; }}
    #qsc-live-root button#qsc-mute {{ background: transparent; border:1px solid rgba(212,175,55,0.3); }}
    #qsc-live-root .status {{ color:#7e9186; font-size:0.85rem; margin-top:10px; min-height:1.2em; }}
    #qsc-live-root .warn {{ color:#ffcf7a; font-size:0.85rem; }}
    #qsc-live-root .callbar {{ display:flex; align-items:center; gap:14px; margin-bottom:16px; }}
    #qsc-live-root .orb {{ width:46px; height:46px; border-radius:50%; flex-shrink:0;
      background: radial-gradient(circle at 35% 30%, #3fce85, #14512f 75%);
      box-shadow: 0 0 0 rgba(46,204,113,0.5); display:flex; align-items:center; justify-content:center; font-size:1.3rem; }}
    #qsc-live-root .orb.live {{ animation: qsc-pulse 1.4s ease-out infinite; }}
    @keyframes qsc-pulse {{
      0% {{ box-shadow: 0 0 0 0 rgba(46,204,113,0.45); }}
      70% {{ box-shadow: 0 0 0 14px rgba(46,204,113,0); }}
      100% {{ box-shadow: 0 0 0 0 rgba(46,204,113,0); }}
    }}
    #qsc-live-root .score {{ font-weight:600; color:#d4af37; }}
  </style>

  <div class="callbar">
    <div class="orb" id="qsc-orb">🎙️</div>
    <div>
      <div style="font-weight:600;">Live Voice Call — free, real-time</div>
      <div style="font-size:0.8rem;color:#7e9186;">Recites with you and talks back — no API key, no cost.</div>
    </div>
    <div style="margin-left:auto;" class="score" id="qsc-score">0%</div>
  </div>

  <div class="ref" id="qsc-ref"></div>
  <div style="margin-top:16px;">
    <button id="qsc-start">📞 Start call</button>
    <button id="qsc-stop" disabled>⏹ End call</button>
    <button id="qsc-reset">↺ Reset</button>
    <button id="qsc-mute">🔊 Voice: on</button>
  </div>
  <div class="status" id="qsc-status">Not started.</div>

  <script>
  (function() {{
    const refText = {ref_json};
    const langCode = {lang_json};
    const feedbackLangCode = {feedback_lang_json};
    let voiceOn = true;
    let correctCount = 0;

    function speak(text, lang) {{
      if (!voiceOn || !window.speechSynthesis || !text) return;
      try {{
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.lang = lang || feedbackLangCode;
        u.rate = 1.02;
        window.speechSynthesis.speak(u);
      }} catch (e) {{ /* speechSynthesis unsupported — silently degrade to text-only */ }}
    }}

    function normalizeArabic(text) {{
      if (!text) return '';
      text = text.replace(/[\\u0610-\\u061A\\u064B-\\u065F\\u06D6-\\u06DC\\u06DF-\\u06E8\\u06EA-\\u06ED\\u08D4-\\u08E1\\u08E3-\\u08FF]/g, '');
      text = text.replace(/\\u0640/g, '');
      text = text.replace(/[إأآا]/g, 'ا');
      text = text.replace(/ى/g, 'ي').replace(/ة/g, 'ه');
      text = text.replace(/\\s+/g, ' ').trim();
      return text;
    }}

    const rawWords = refText.split(/\\s+/).filter(Boolean);
    const normWords = rawWords.map(normalizeArabic);
    const refEl = document.getElementById('qsc-ref');
    refEl.innerHTML = rawWords.map((w, i) => `<span class="w pending" id="qsc-w-${{i}}">${{w}}</span>`).join(' ');

    const statusEl = document.getElementById('qsc-status');
    const startBtn = document.getElementById('qsc-start');
    const stopBtn = document.getElementById('qsc-stop');
    const resetBtn = document.getElementById('qsc-reset');

    let refIndex = 0;
    let active = false;
    let recognition = null;

    function markWord(i, cls) {{
      const el = document.getElementById('qsc-w-' + i);
      if (el) el.className = 'w ' + cls;
    }}

    const orbEl = document.getElementById('qsc-orb');
    const scoreEl = document.getElementById('qsc-score');
    const muteBtn = document.getElementById('qsc-mute');

    function updateScore() {{
      const attempted = refIndex;
      const pct = attempted > 0 ? Math.round((correctCount / attempted) * 100) : 0;
      scoreEl.textContent = pct + '%';
    }}

    function resetAll() {{
      refIndex = 0;
      correctCount = 0;
      window.speechSynthesis && window.speechSynthesis.cancel();
      for (let i = 0; i < rawWords.length; i++) markWord(i, 'pending');
      updateScore();
      statusEl.textContent = active ? 'Listening...' : 'Not started.';
    }}

    function handleFinalTranscript(transcript) {{
      const said = normalizeArabic(transcript).split(/\\s+/).filter(Boolean);
      let anyWrong = false;
      for (const word of said) {{
        if (refIndex >= normWords.length) break;
        if (word === normWords[refIndex]) {{
          markWord(refIndex, 'correct');
          correctCount++;
        }} else {{
          markWord(refIndex, 'wrong');
          anyWrong = true;
        }}
        refIndex++;
      }}
      updateScore();
      if (refIndex >= normWords.length) {{
        statusEl.textContent = 'Ayah complete — tap Reset to go again.';
        const pct = Math.round((correctCount / normWords.length) * 100);
        orbEl.classList.remove('live');
        if (pct >= 90) speak('Excellent recitation! ' + pct + ' percent.', feedbackLangCode);
        else if (pct >= 60) speak('Good effort — ' + pct + ' percent. Try it again for a higher score.', feedbackLangCode);
        else speak('Let\\'s try that ayah again, a little slower.', feedbackLangCode);
      }} else if (anyWrong) {{
        speak('Try again: ' + rawWords[refIndex - 1], langCode);
      }}
    }}

    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {{
      statusEl.innerHTML = '<span class="warn">Live Mode needs Chrome or Edge (desktop or Android) — this browser doesn\\'t support it. Use Practice Mode below instead — it gives the same accurate word-by-word correction.</span>';
      startBtn.disabled = true;
    }} else {{
      muteBtn.addEventListener('click', function() {{
        voiceOn = !voiceOn;
        muteBtn.textContent = voiceOn ? '🔊 Voice: on' : '🔇 Voice: off';
        if (!voiceOn && window.speechSynthesis) window.speechSynthesis.cancel();
      }});

      startBtn.addEventListener('click', function() {{
        active = true;
        resetAll();
        orbEl.classList.add('live');
        speak('Starting. Recite when ready.', feedbackLangCode);
        recognition = new SR();
        recognition.lang = langCode;
        recognition.continuous = true;
        recognition.interimResults = true;

        recognition.onresult = function(event) {{
          for (let i = event.resultIndex; i < event.results.length; i++) {{
            const result = event.results[i];
            if (result.isFinal) {{
              handleFinalTranscript(result[0].transcript);
            }} else {{
              statusEl.textContent = 'Hearing: ' + result[0].transcript;
            }}
          }}
        }};
        recognition.onerror = function(event) {{
          if (event.error === 'not-allowed' || event.error === 'permission-denied') {{
            statusEl.innerHTML = '<span class="warn">Microphone permission was blocked. Allow mic access for this page and press Start again.</span>';
            active = false;
          }} else if (event.error !== 'no-speech') {{
            statusEl.textContent = 'Recognition hiccup (' + event.error + ') — restarting...';
          }}
        }};
        recognition.onend = function() {{
          if (active) {{
            try {{ recognition.start(); }} catch (e) {{ /* already starting */ }}
          }}
        }};

        try {{
          recognition.start();
          statusEl.textContent = 'Listening...';
          startBtn.disabled = true;
          stopBtn.disabled = false;
        }} catch (e) {{
          statusEl.innerHTML = '<span class="warn">Could not start: ' + e.message + '</span>';
        }}
      }});

      stopBtn.addEventListener('click', function() {{
        active = false;
        if (recognition) recognition.stop();
        if (window.speechSynthesis) window.speechSynthesis.cancel();
        orbEl.classList.remove('live');
        statusEl.textContent = 'Call ended.';
        startBtn.disabled = false;
        stopBtn.disabled = true;
      }});

      resetBtn.addEventListener('click', resetAll);
    }}
  }})();
  </script>
</div>
"""
