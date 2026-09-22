# 📖 Quran Study Companion

A Streamlit web app to **read, listen, and reflect** on the Qur'an — with an AI
chatbot grounded in real Qur'an/Hadith text, daily learning goals, pre-recorded
recitations from famous reciters (Mishary Alafasy, Abdul Basit, Al-Husary,
Al-Sudais and more), and a recitation coach that gives you word-by-word
pronunciation feedback in Arabic, Urdu, or English.

Emerald-green, curved-card UI to match the reference dashboard design.

---

## ✨ Features

| Feature | Where | Notes |
|---|---|---|
| Dashboard with Verse of the Day | `app.py` | Rotates daily, deterministic |
| Daily goals + streak + points | `app.py`, `database/db.py` | Local SQLite, no server needed |
| Sidebar Settings (reciter, translation, text size, transliteration) | `utils/helpers.py` → `render_sidebar_settings()` | One panel, used on every page, sticks as you navigate |
| Browse every surah, any translation, ayah-range slider | `app_pages/1_📖_Browse_Quran.py` | Arabic + English + Urdu |
| 9 famous reciters, full surah + per-ayah audio | `app_pages/1_📖_Browse_Quran.py` | Streamed free from Al Quran Cloud CDN |
| AI Companion chatbot (Quran + Hadith aware) | `app_pages/2_🤖_AI_Companion.py`, `services/ai_chat.py` | Grounded / cites sources |
| Recitation Coach — Practice Mode (accurate) | `app_pages/3_🎙️_Recitation_Coach.py`, `services/recitation_coach.py` | Record → transcribe → word-by-word score |
| Recitation Coach — Live Mode (experimental) | same page, `build_live_mode_html()` | Continuous browser speech recognition, free, Chrome/Edge only — see honesty note below |
| Urdu voice feedback | `services/tts.py` | Free gTTS |
| Settings (AI status, reset progress) | `app_pages/4_⚙️_Settings.py` | Persisted in SQLite |

---

## 🗂️ Project structure — what's where

```
quran-study-companion/
├── app.py                        # Entry point = Dashboard/Home page
├── config.py                     # ALL settings live here: colors, reciters, models, etc.
├── requirements.txt
├── .env.example                  # Copy to .env and fill in your API key
├── .gitignore
├── assets/
│   └── style.css                 # Emerald gradient + curved-card theme
├── database/
│   └── db.py                     # SQLite: goals, streak, chat history, recitation log
├── services/                     # All external calls live here (nowhere else)
│   ├── quran_api.py               # Free Quran text + audio (Al Quran Cloud)
│   ├── hadith_api.py              # Free Hadith text (fawazahmed0/hadith-api)
│   ├── ai_chat.py                  # Claude API + grounding logic ("accuracy" layer)
│   ├── tts.py                      # Free text-to-speech (gTTS)
│   └── recitation_coach.py         # Local speech-to-text + word-diff scoring
├── app_pages/                     # Every sidebar page after Home
│   ├── 1_📖_Browse_Quran.py
│   ├── 2_🤖_AI_Companion.py
│   ├── 3_🎙️_Recitation_Coach.py
│   └── 4_⚙️_Settings.py
├── utils/
│   └── helpers.py                 # CSS injection, Arabic normalization, streak math
└── data/
    └── app.db                     # Created automatically on first run
```

**Rule of thumb for adding new features:** if it talks to an external API, it
goes in `services/`. If it's a new screen, it goes in `app_pages/`. If it's a
constant (a new reciter, a new color), it goes in `config.py`.

---

## 🚀 Step-by-step setup (local)

### 1. Install Python
You need **Python 3.10+**. Check with `python3 --version`.

### 2. Get the code onto your machine
If you're starting from this folder, skip to step 3. Otherwise:
```bash
git clone https://github.com/<your-username>/quran-study-companion.git
cd quran-study-companion
```

### 3. Create a virtual environment (keeps dependencies isolated)
```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```
> First run of the Recitation Coach will download a small speech-recognition
> model (a few hundred MB) automatically — that's normal and only happens once.

### 5. Get an AI key (Gemini is free — default; Claude is paid, optional)

**Default: Gemini (free tier, no card needed)**
1. Go to [aistudio.google.com](https://aistudio.google.com), sign in with a Google account.
2. Click **Get API key → Create API key**.
3. Copy `.env.example` to `.env` (`cp .env.example .env`) and paste it into `GEMINI_API_KEY`.

That's it — `AI_PROVIDER=gemini` is already the default in `.env.example`.

**Alternative: Claude (paid — needs credits)**
If you'd rather use Claude, get a key at [console.anthropic.com](https://console.anthropic.com),
add credits under Plans & Billing ($5 minimum — there's no permanent free
API tier, only a small one-time trial credit on new accounts), paste the key
into `ANTHROPIC_API_KEY` in `.env`, and set `AI_PROVIDER=anthropic`. You can
flip back to Gemini any time by changing that one line — no code changes.

### 6. Run the app
```bash
streamlit run app.py
```
It opens at `http://localhost:8501`. The sidebar shows Home, Browse Quran, AI
Companion, Recitation Coach, and Settings — matching the reference layout.

---

## 🩹 Fixing `ModuleNotFoundError: No module named 'utils'` (or `config`, `services`, `database`)

If you see this on Streamlit Cloud, it means the deployed copy of your repo
is missing one of the shared folders (`utils/`, `services/`, `database/`,
`assets/`) — almost always because a drag-and-drop upload through GitHub's
web UI flattened the folder structure instead of preserving it (very common
when uploading from a phone browser). Every page file in this project now
also carries a defensive fix at the very top:
```python
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
```
This guarantees the project root is importable regardless of how Streamlit
resolves the page's working directory — but it can't fix a folder that
genuinely isn't in your repo. **Check your repo on GitHub.com first:** open
it in the browser and confirm you see `utils/`, `services/`, `database/`,
and `assets/` as actual folders (clickable, with files inside), not just
loose `.py` files sitting at the top level. If a folder is missing or flat,
the most reliable fix with zero tools is to recreate it file-by-file using
GitHub's **Add file → Create new file** button and **typing the full path
with slashes as the filename** (e.g. type `utils/helpers.py` as the
filename) — GitHub creates the folder automatically from the path, so this
can't flatten no matter what browser or device you're on. Paste in the
matching file's content from your unzipped project and commit.

---

## ☁️ Deploying for free (so you can share a link)

**Streamlit Community Cloud** (free, made for exactly this):
1. Push this project to a **public GitHub repo** (steps below).
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **New app**, pick your repo, branch `main`, main file `app.py`.
4. Under **Advanced settings → Secrets**, paste:
   ```
   GEMINI_API_KEY = "your-gemini-key"
   ```
   (or, if using Claude instead: `AI_PROVIDER = "anthropic"` and `ANTHROPIC_API_KEY = "sk-ant-..."`)
   Add `DEEPGRAM_API_KEY = "..."` too if you set up Live Call Mode.
5. Click **Deploy**. You'll get a public `https://<something>.streamlit.app` link.

> Note: the free tier has limited CPU/RAM. If the Recitation Coach feels slow
> there, set `WHISPER_MODEL_SIZE=tiny` in your secrets for a lighter model.

---

## 📤 Pushing this to GitHub (step by step)

```bash
cd quran-study-companion
git init
git add .
git commit -m "Initial commit: Quran Study Companion"
git branch -M main
git remote add origin https://github.com/<your-username>/quran-study-companion.git
git push -u origin main
```
`.env` is already excluded via `.gitignore` — your API key will **not** be
pushed. Double-check with `git status` before your first commit.

---

## 🧠 How the AI Companion stays accurate

Plain LLM calls can hallucinate a verse's wording — a serious problem for a
Qur'an app. So `services/ai_chat.py` doesn't just forward your question to
Claude. It first:

1. Scans your message for a reference (`2:255`, `Surah Yasin ayah 5`,
   `Bukhari 1`, etc.).
2. If found, fetches the **real text** from the Al Quran Cloud / Hadith APIs.
3. Hands that verified text to Claude as context and instructs it (via the
   system prompt) to quote scripture **only** from that context — and to say
   "I can't verify that exact wording here" rather than guess, if nothing was
   retrieved.
4. For fiqh (jurisprudence) questions, the system prompt tells Claude to
   present the mainstream positions and their differences rather than state
   one ruling as universal fact, and to point you to a qualified scholar for
   a binding personal ruling.

This is "RAG-lite," not a certified religious authority — always double-check
anything important against a trusted source or scholar.

---

## 🎙️ Recitation Coach — two modes, and the honest trade-off between them

**Practice Mode** (the reliable one): you record a short clip (`st.audio_input`
— built into Streamlit, no extra setup), `faster-whisper` (free, runs locally
on CPU) transcribes it, and `services/recitation_coach.py` diffs your
transcript against the correct ayah word-by-word (`difflib`), after
normalizing Arabic text (stripping diacritics, unifying alef/ya/ta-marbuta
variants) so it flags real mistakes without being overly strict about minor
tajweed marks. You get colour-coded feedback + a spoken tip (`gTTS`) in
1–3 seconds. This is chunk-based, not continuous — but tested and accurate.

**Live Mode (beta)** — the closer-to-a-real-live-call attempt: it uses the
browser's own **free, built-in Web Speech API** (`build_live_mode_html()` in
`services/recitation_coach.py`, rendered via `st.components.v1.html`) to
listen continuously and light up reference words green/red *as you recite*,
with no per-chunk round trip. Two things to know before you rely on it:
- **Browser support:** Chrome or Edge only (desktop or Android) — no Safari,
  no Firefox. The component detects unsupported browsers and says so rather
  than silently doing nothing.
- **Recognition quality:** it uses the browser's general-purpose Arabic
  speech model, not one trained on tajweed-precise Quranic recitation, and
  the word-matching is a simple greedy left-to-right pass (no backtracking)
  — so it's a good "am I roughly flowing correctly, live" signal, not a
  tajweed-grade judge. Practice Mode is the more precise, fully-tested
  option; think of Live Mode as the live/continuous bonus layer on top.

## 📞 Live Call Mode — the "at any cost" paid option

If free isn't the constraint, `services/live_stream_coach.py` gives you the
real thing: continuous WebRTC mic streaming (`streamlit-webrtc`) piped live
to **Deepgram**'s streaming transcription — works in every browser (not just
Chrome), far more stable and accurate than the free Web Speech API. Get a
free-trial key at console.deepgram.com (a few dollars of paid usage after
that covers a lot of practice), add `DEEPGRAM_API_KEY` to your `.env` /
Secrets, `pip install streamlit-webrtc deepgram-sdk streamlit-autorefresh av
numpy`, and the "📞 Live Call Mode" section on Recitation Coach lights up.

**What paying does *not* buy:** a model that judges tajweed (makhraj, madd
length, qalqalah) the way a human teacher does. No service — free or paid —
does that off-the-shelf; it needs a custom model trained on
tajweed-annotated audio. Every option in this app, including this one, gives
you accurate live *word matching*, not a tajweed examiner.

**One honesty note:** this file wires together WebRTC threading, a
persistent websocket, and a polling UI refresh — three moving parts I
followed the documented pattern for but couldn't run end-to-end in a real
browser to verify from here. Test it locally before relying on it; Practice
Mode and the free Live Mode are the tested fallbacks if anything breaks.

There's also a real technical ceiling worth knowing about: `st.components.v1.html`
renders your component inside a sandboxed iframe, and microphone access
(`getUserMedia`, which `SpeechRecognition` needs) requires that iframe to be
granted a `microphone` permissions policy. Whether Streamlit's iframe grants
that can vary by Streamlit version/browser — if Live Mode's Start button
does nothing or the browser never prompts for mic access, that's why. If you
want to push past this ceiling:

- **Fix the iframe permission properly:** package this as a real Streamlit
  custom component (`streamlit.components.v1.declare_component`) instead of
  raw `components.v1.html` — custom components get more control over their
  iframe's permissions policy.
- **True streaming ASR, cloud-grade:** replace the Web Speech API with a
  paid streaming speech-to-text service (e.g. a cloud provider's streaming
  STT) fed through `streamlit-webrtc` — the biggest step up, and typically
  not free.
- **Real tajweed rule-checking** (madd length, qalqalah, idgham, etc.), not
  just "right/wrong word" — needs a phoneme-level model trained on
  tajweed-annotated Qur'an audio (research-level; look at Tarteel.ai's
  public work for inspiration).
- **Per-user accounts** instead of one shared local SQLite file, if you want
  multiple people to have separate streaks — swap `database/db.py` for a
  hosted Postgres (Supabase has a free tier) and add simple auth.

---

## 🙏 Free data sources used (please keep attribution)

- **Qur'an text & audio:** [Al Quran Cloud](https://alquran.cloud) — free,
  unauthenticated REST API + CDN (`api.alquran.cloud`, `cdn.islamic.network`),
  a project by Islamic Network.
- **Hadith text:** [fawazahmed0/hadith-api](https://github.com/fawazahmed0/hadith-api)
  — free, unauthenticated, served via jsDelivr.
- **AI Companion:** [Claude API](https://console.anthropic.com) (Anthropic).
- **Text-to-speech:** [gTTS](https://github.com/pndurette/gTTS).
- **Speech-to-text:** [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
  (CTranslate2 reimplementation of OpenAI's Whisper).

Both free APIs ask that you keep them credited if you publish the project —
this README and the in-app captions already do that; please keep it that way
in anything you submit.

---

## 🛠️ Extending the app

- **Add a reciter:** find its edition identifier at
  `https://api.alquran.cloud/v1/edition/format/audio`, add it to
  `RECITERS` in `config.py`.
- **Add a translation language:** same idea — browse
  `https://api.alquran.cloud/v1/edition/type/translation`, add to
  `TRANSLATION_EDITIONS` in `config.py`.
- **Add a hadith collection:** add its `eng-*`/`urd-*` edition ids (see
  `https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions.json`) to
  `HADITH_COLLECTIONS` in `config.py`.
- **Change the color theme:** everything is in `assets/style.css` and the
  `THEME` dict in `config.py`.
- **Add a new page:** drop a new file in `app_pages/`, prefixed with a number so
  it sits in the right sidebar order (e.g. `5_📊_Progress.py`).

---

## ⚠️ Disclaimer

This is a study tool, not a religious authority. Recitation feedback and AI
answers can be imperfect — always verify important matters (especially fiqh
rulings) with a qualified scholar or a trusted mushaf/hadith collection.
