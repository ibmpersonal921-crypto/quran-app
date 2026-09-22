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
      - speechSynthesis (TTS) to talk back with short spoken coaching cues,
        so it feels like a live call rather than a silent transcript.

    Two correctness fixes over a naive version of this:
      1. The mic is paused while the coach is speaking and resumed right
         after, so the coach never hears (and reacts to) its own voice —
         without this, TTS output leaking into the mic causes cascading
         false "wrong" marks and erratic restarts.
      2. Word matching is fuzzy (small edit-distance tolerance), not exact
         string equality — browser Arabic speech recognition is noisy, and
         exact matching marks correct recitation as wrong on every minor
         misheard letter.

    No API key, no server, no cost: both APIs ship in the browser
    (Chrome/Edge; Web Speech needs an internet connection to the browser's
    recognition service under the hood, but there's no key to manage and
    nothing to pay for).
    """
    import json

    ref_json = json.dumps(reference_arabic)
    lang_json = json.dumps(lang_code)
    feedback_lang_json = json.dumps(feedback_lang)

    return f"""
<div id="qsc-live-root" style="font-family:'Poppins',sans-serif;color:#f4f7f5;background:linear-gradient(160deg,#0f2c22,#123527);border:1px solid rgba(212,175,55,0.18);border-radius:22px;padding:24px 26px;">
  <style>
    #qsc-live-root .ref {{ font-family:'Amiri','Traditional Arabic',serif; direction:rtl; text-align:right; line-height:2.8; font-size:1.75rem; padding:18px 4px; }}
    #qsc-live-root .w {{ display:inline-block; margin:3px 5px; padding:4px 10px; border-radius:999px; transition: all .15s ease; }}
    #qsc-live-root .pending {{ color:#b9c9c0; }}
    #qsc-live-root .current {{ background:rgba(212,175,55,0.16); color:#ffe9a8; border:1px solid rgba(212,175,55,0.5); box-shadow:0 0 0 3px rgba(212,175,55,0.08); }}
    #qsc-live-root .correct {{ background:rgba(46,204,113,0.15); color:#7CE8A6; border:1px solid rgba(46,204,113,0.35); }}
    #qsc-live-root .wrong {{ background:rgba(231,76,60,0.15); color:#ff8f80; border:1px solid rgba(231,76,60,0.35); }}
    #qsc-live-root button {{ background:linear-gradient(135deg,#1f7a4d,#14512f); color:#f4f7f5; border:1px solid rgba(212,175,55,0.25); border-radius:999px; padding:0.55em 1.4em; font-weight:500; font-size:0.9rem; cursor:pointer; margin-right:8px; transition: transform .12s ease, filter .12s ease; }}
    #qsc-live-root button:hover:not(:disabled) {{ filter:brightness(1.12); transform: translateY(-1px); }}
    #qsc-live-root button:disabled {{ opacity:0.4; cursor:not-allowed; }}
    #qsc-live-root button#qsc-mute {{ background: transparent; border:1px solid rgba(212,175,55,0.3); }}
    #qsc-live-root .status {{ color:#9fb3a8; font-size:0.85rem; margin-top:4px; min-height:1.2em; }}
    #qsc-live-root .warn {{ color:#ffcf7a; font-size:0.85rem; }}
    #qsc-live-root .callbar {{ display:flex; align-items:center; gap:14px; margin-bottom:6px; }}
    #qsc-live-root .orb {{ width:50px; height:50px; border-radius:50%; flex-shrink:0;
      background: radial-gradient(circle at 35% 30%, #3fce85, #14512f 75%);
      box-shadow: 0 0 0 rgba(46,204,113,0.5); display:flex; align-items:center; justify-content:center; font-size:1.4rem; }}
    #qsc-live-root .orb.live {{ animation: qsc-pulse 1.4s ease-out infinite; }}
    #qsc-live-root .orb.speaking {{ animation: qsc-pulse-gold 0.9s ease-out infinite; }}
    @keyframes qsc-pulse {{
      0% {{ box-shadow: 0 0 0 0 rgba(46,204,113,0.45); }}
      70% {{ box-shadow: 0 0 0 14px rgba(46,204,113,0); }}
      100% {{ box-shadow: 0 0 0 0 rgba(46,204,113,0); }}
    }}
    @keyframes qsc-pulse-gold {{
      0% {{ box-shadow: 0 0 0 0 rgba(212,175,55,0.55); }}
      70% {{ box-shadow: 0 0 0 12px rgba(212,175,55,0); }}
      100% {{ box-shadow: 0 0 0 0 rgba(212,175,55,0); }}
    }}
    #qsc-live-root .score {{ font-weight:700; color:#d4af37; font-size:1.15rem; }}
    #qsc-live-root .score-label {{ font-size:0.7rem; color:#7e9186; text-transform:uppercase; letter-spacing:0.05em; text-align:right; }}
    #qsc-live-root .meta {{ display:flex; justify-content:space-between; align-items:baseline; margin-top:2px; }}
    #qsc-live-root .timer {{ font-size:0.8rem; color:#7e9186; font-variant-numeric: tabular-nums; }}
    #qsc-live-root .progress-track {{ height:6px; border-radius:999px; background:rgba(255,255,255,0.06); margin-top:14px; overflow:hidden; }}
    #qsc-live-root .progress-fill {{ height:100%; width:0%; border-radius:999px; background:linear-gradient(90deg,#2ecc71,#d4af37); transition: width .25s ease; }}
    #qsc-live-root .caption {{ margin-top:14px; background:rgba(0,0,0,0.18); border:1px solid rgba(255,255,255,0.06); border-radius:12px; padding:10px 14px; font-size:0.9rem; color:#cfe0d6; min-height:2.4em; }}
    #qsc-live-root .caption .tag {{ font-size:0.68rem; text-transform:uppercase; letter-spacing:0.06em; color:#7e9186; display:block; margin-bottom:2px; }}
    #qsc-live-root .legend {{ display:flex; gap:16px; margin-top:10px; font-size:0.75rem; color:#8fa398; }}
    #qsc-live-root .legend span {{ display:inline-flex; align-items:center; gap:6px; }}
    #qsc-live-root .legend i {{ width:10px; height:10px; border-radius:50%; display:inline-block; }}
    #qsc-live-root .controls {{ margin-top:18px; }}
  </style>

  <div class="callbar">
    <div class="orb" id="qsc-orb">🎙️</div>
    <div style="flex:1;">
      <div style="font-weight:600;">Live Voice Call</div>
      <div style="font-size:0.78rem;color:#7e9186;">Free, real-time — recites with you and talks back.</div>
    </div>
    <div>
      <div class="score" id="qsc-score">0%</div>
      <div class="score-label">accuracy</div>
    </div>
  </div>
  <div class="meta">
    <div class="timer" id="qsc-timer">00:00</div>
    <div class="timer" id="qsc-progress-label">0 words</div>
  </div>
  <div class="progress-track"><div class="progress-fill" id="qsc-progress"></div></div>

  <div class="ref" id="qsc-ref"></div>

  <div class="caption" id="qsc-caption"><span class="tag">Coach</span>Press "Start call" and recite when ready.</div>

  <div class="legend">
    <span><i style="background:#7CE8A6;"></i>Matched</span>
    <span><i style="background:#ff8f80;"></i>Needs work</span>
    <span><i style="background:#ffe9a8;"></i>Up next</span>
  </div>

  <div class="controls">
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
    let speaking = false;
    let wantListening = false;   // user intent: call is on
    let recognizing = false;     // recognition.start() actually in flight

    // --- Small Levenshtein distance, used for forgiving word matching ---
    // (browser Arabic speech recognition regularly mis-hears a single
    // letter/diacritic even on a perfectly correct recitation, so exact
    // string equality was marking correct words as wrong)
    function editDistance(a, b) {{
      const m = a.length, n = b.length;
      if (m === 0) return n;
      if (n === 0) return m;
      const dp = new Array(n + 1);
      for (let j = 0; j <= n; j++) dp[j] = j;
      for (let i = 1; i <= m; i++) {{
        let prev = dp[0];
        dp[0] = i;
        for (let j = 1; j <= n; j++) {{
          const tmp = dp[j];
          dp[j] = Math.min(
            dp[j] + 1,
            dp[j - 1] + 1,
            prev + (a[i - 1] === b[j - 1] ? 0 : 1)
          );
          prev = tmp;
        }}
      }}
      return dp[n];
    }}
    function isCloseMatch(said, expected) {{
      if (said === expected) return true;
      const tolerance = expected.length <= 3 ? 0 : (expected.length <= 6 ? 1 : 2);
      return editDistance(said, expected) <= tolerance;
    }}

    function pad2(n) {{ return n < 10 ? '0' + n : '' + n; }}
    let elapsedSec = 0;
    let timerHandle = null;
    function startTimer() {{
      elapsedSec = 0;
      if (timerHandle) clearInterval(timerHandle);
      timerHandle = setInterval(function() {{
        elapsedSec++;
        const m = Math.floor(elapsedSec / 60), s = elapsedSec % 60;
        const t = document.getElementById('qsc-timer');
        if (t) t.textContent = pad2(m) + ':' + pad2(s);
      }}, 1000);
    }}
    function stopTimer() {{
      if (timerHandle) clearInterval(timerHandle);
      timerHandle = null;
    }}

    function setCaption(tag, text) {{
      const el = document.getElementById('qsc-caption');
      if (el) el.innerHTML = '<span class="tag">' + tag + '</span>' + text;
    }}

    const orbEl = document.getElementById('qsc-orb');

    // Speaking pauses the mic and resumes it afterwards, so the coach's own
    // voice through the speakers never gets picked back up by the mic and
    // mistaken for the reciter's next word.
    function speak(text, lang, tag) {{
      if (!text) return;
      if (tag) setCaption(tag, text);
      if (!voiceOn || !window.speechSynthesis) return;
      try {{
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.lang = lang || feedbackLangCode;
        u.rate = 1.0;
        speaking = true;
        orbEl.classList.remove('live');
        orbEl.classList.add('speaking');
        if (recognition && recognizing) {{
          try {{ recognition.stop(); }} catch (e) {{}}
        }}
        u.onend = u.onerror = function() {{
          speaking = false;
          orbEl.classList.remove('speaking');
          if (wantListening) {{
            orbEl.classList.add('live');
            safeStartRecognition();
          }}
        }};
        window.speechSynthesis.speak(u);
      }} catch (e) {{ /* speechSynthesis unsupported — captions still show */ }}
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
    document.getElementById('qsc-progress-label').textContent = '0 / ' + rawWords.length + ' words';

    const statusEl = document.getElementById('qsc-status');
    const startBtn = document.getElementById('qsc-start');
    const stopBtn = document.getElementById('qsc-stop');
    const resetBtn = document.getElementById('qsc-reset');
    const scoreEl = document.getElementById('qsc-score');
    const progressEl = document.getElementById('qsc-progress');
    const progressLabelEl = document.getElementById('qsc-progress-label');
    const muteBtn = document.getElementById('qsc-mute');

    let refIndex = 0;
    let recognition = null;

    function markWord(i, cls) {{
      const el = document.getElementById('qsc-w-' + i);
      if (el) el.className = 'w ' + cls;
    }}
    function highlightCurrent() {{
      if (refIndex < rawWords.length) markWord(refIndex, 'current');
    }}

    function updateScore() {{
      const attempted = refIndex;
      const pct = attempted > 0 ? Math.round((correctCount / attempted) * 100) : 0;
      scoreEl.textContent = pct + '%';
      progressEl.style.width = Math.round((refIndex / rawWords.length) * 100) + '%';
      progressLabelEl.textContent = refIndex + ' / ' + rawWords.length + ' words';
    }}

    function resetAll() {{
      refIndex = 0;
      correctCount = 0;
      window.speechSynthesis && window.speechSynthesis.cancel();
      for (let i = 0; i < rawWords.length; i++) markWord(i, 'pending');
      highlightCurrent();
      updateScore();
      statusEl.textContent = wantListening ? 'Listening...' : 'Not started.';
    }}

    function handleFinalTranscript(transcript) {{
      const said = normalizeArabic(transcript).split(/\\s+/).filter(Boolean);
      let anyWrong = false;
      for (const word of said) {{
        if (refIndex >= normWords.length) break;
        if (isCloseMatch(word, normWords[refIndex])) {{
          markWord(refIndex, 'correct');
          correctCount++;
        }} else {{
          markWord(refIndex, 'wrong');
          anyWrong = true;
        }}
        refIndex++;
      }}
      updateScore();
      highlightCurrent();
      if (refIndex >= normWords.length) {{
        stopTimer();
        const pct = Math.round((correctCount / normWords.length) * 100);
        statusEl.textContent = 'Ayah complete — tap Reset to go again.';
        if (pct >= 90) speak('Excellent recitation — ' + pct + ' percent.', feedbackLangCode, 'Coach');
        else if (pct >= 60) speak('Good effort — ' + pct + ' percent. Try it again for a higher score.', feedbackLangCode, 'Coach');
        else speak("Let's try that ayah again, a little slower.", feedbackLangCode, 'Coach');
      }} else if (anyWrong) {{
        setCaption('Heard', transcript);
        speak('Keep going, try that word again.', feedbackLangCode, 'Coach');
      }} else {{
        setCaption('Heard', transcript);
      }}
    }}

    function safeStartRecognition() {{
      if (!wantListening || speaking || recognizing || !recognition) return;
      try {{
        recognition.start();
      }} catch (e) {{
        // Already starting/started — Chrome throws InvalidStateError if
        // start() is called too close together; a short retry is enough.
        setTimeout(function() {{
          if (wantListening && !speaking && !recognizing) {{
            try {{ recognition.start(); }} catch (e2) {{}}
          }}
        }}, 300);
      }}
    }}

    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {{
      statusEl.innerHTML = '<span class="warn">Live Mode needs Chrome or Edge (desktop or Android) — this browser doesn\\'t support it. Use Practice Mode below instead — it gives the same accurate word-by-word correction.</span>';
      startBtn.disabled = true;
    }} else {{
      recognition = new SR();
      recognition.lang = langCode;
      recognition.continuous = true;
      recognition.interimResults = true;

      recognition.onstart = function() {{ recognizing = true; }};

      recognition.onresult = function(event) {{
        for (let i = event.resultIndex; i < event.results.length; i++) {{
          const result = event.results[i];
          if (result.isFinal) {{
            handleFinalTranscript(result[0].transcript);
          }} else {{
            setCaption('Hearing', result[0].transcript);
          }}
        }}
      }};
      recognition.onerror = function(event) {{
        if (event.error === 'not-allowed' || event.error === 'permission-denied') {{
          statusEl.innerHTML = '<span class="warn">Microphone permission was blocked. Allow mic access for this page and press Start again.</span>';
          wantListening = false;
        }} else if (event.error !== 'no-speech' && event.error !== 'aborted') {{
          statusEl.textContent = 'Recognition hiccup (' + event.error + ') — recovering...';
        }}
      }};
      recognition.onend = function() {{
        recognizing = false;
        if (wantListening && !speaking) {{
          setTimeout(safeStartRecognition, 150);
        }}
      }};

      muteBtn.addEventListener('click', function() {{
        voiceOn = !voiceOn;
        muteBtn.textContent = voiceOn ? '🔊 Voice: on' : '🔇 Voice: off';
        if (!voiceOn && window.speechSynthesis) window.speechSynthesis.cancel();
      }});

      startBtn.addEventListener('click', function() {{
        wantListening = true;
        resetAll();
        orbEl.classList.add('live');
        startTimer();
        startBtn.disabled = true;
        stopBtn.disabled = false;
        statusEl.textContent = 'Listening...';
        speak('Starting. Recite when ready.', feedbackLangCode, 'Coach');
        // speak() above pauses the mic and resumes it on its own once the
        // greeting finishes, via the onend handler wired into speak().
      }});

      stopBtn.addEventListener('click', function() {{
        wantListening = false;
        stopTimer();
        if (recognition) {{ try {{ recognition.stop(); }} catch (e) {{}} }}
        if (window.speechSynthesis) window.speechSynthesis.cancel();
        speaking = false;
        orbEl.classList.remove('live');
        orbEl.classList.remove('speaking');
        statusEl.textContent = 'Call ended.';
        setCaption('Coach', 'Call ended. Press "Start call" to go again.');
        startBtn.disabled = false;
        stopBtn.disabled = true;
      }});

      resetBtn.addEventListener('click', resetAll);
      highlightCurrent();
    }}
  }})();
  </script>
</div>
"""
