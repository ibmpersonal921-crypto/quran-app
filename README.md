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
| Browse every surah, any translation | `pages/1_📖_Browse_Quran.py` | Arabic + English + Urdu |
| 9 famous reciters, full surah + per-ayah audio | `pages/1_📖_Browse_Quran.py` | Streamed free from Al Quran Cloud CDN |
| AI Companion chatbot (Quran + Hadith aware) | `pages/2_🤖_AI_Companion.py`, `services/ai_chat.py` | Grounded / cites sources |
| Recitation Coach with live-style correction | `pages/3_🎙️_Recitation_Coach.py`, `services/recitation_coach.py` | Near-real-time, see honesty note below |
| Urdu voice feedback | `services/tts.py` | Free gTTS |
| Settings (reciter, translation, feedback voice) | `pages/4_⚙️_Settings.py` | Persisted in SQLite |

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
├── pages/                         # Every sidebar page after Home
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
goes in `services/`. If it's a new screen, it goes in `pages/`. If it's a
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

### 5. Get a Claude API key (for the AI Companion)
1. Go to https://console.anthropic.com and sign up.
2. New accounts get some free trial credit — enough to build and demo this
   project without spending anything up front.
3. Create an API key under **Settings → API Keys**.
4. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
5. Paste your key into `.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

**Want it 100% free with no card at all?** The AI Companion is written against
the Claude API by default, but `services/ai_chat.py` only touches Claude in
one place (`_get_client()` and the `client.messages.create(...)` call). You
can swap in Google's **Gemini API** (generous free tier, no card required for
the free tier) or **Groq** (free tier, very fast open models) by rewriting
just that one function — everything else (the grounding/retrieval logic) stays
the same.

### 6. Run the app
```bash
streamlit run app.py
```
It opens at `http://localhost:8501`. The sidebar shows Home, Browse Quran, AI
Companion, Recitation Coach, and Settings — matching the reference layout.

---

## ☁️ Deploying for free (so you can share a link)

**Streamlit Community Cloud** (free, made for exactly this):
1. Push this project to a **public GitHub repo** (steps below).
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **New app**, pick your repo, branch `main`, main file `app.py`.
4. Under **Advanced settings → Secrets**, paste:
   ```
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
   (Streamlit Cloud secrets are read the same way as environment variables —
   `config.py` already uses `os.getenv`, so no code changes needed.)
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

## 🎙️ Recitation Coach — honest scope

A true "live phone call" AI tutor that corrects you word-by-word *while you're
still speaking* needs a **streaming** speech recognizer (partial results every
~200ms). Free, fully local models don't do that reliably for Arabic/tajweed
yet, so this project uses a **near-real-time loop** instead:

1. You record a short clip (`st.audio_input` — built into Streamlit, no extra
   setup) reciting one ayah.
2. `faster-whisper` (free, runs locally on CPU) transcribes it.
3. `services/recitation_coach.py` diffs your transcript against the correct
   ayah word-by-word (`difflib`) and normalizes Arabic text first (strips
   diacritics, unifies alef/ya/ta-marbuta variants) so it flags real mistakes
   without being overly strict about minor tajweed marks.
4. You get colour-coded feedback + a spoken tip (via `gTTS`) in 1–3 seconds.

### Going further (if you want to push past the MVP)
- **True streaming correction:** replace the record→transcribe→diff loop with
  a streaming ASR service (e.g. a cloud provider's streaming speech-to-text)
  fed through `streamlit-webrtc`, so feedback appears while you're still
  talking. This is the biggest engineering step up and typically isn't free.
- **Real tajweed rule-checking** (madd length, qalqalah, idgham, etc.), not
  just "right/wrong word" — this needs a phoneme-level model trained on
  tajweed-annotated Qur'an audio (research-level; e.g. look at Tarteel.ai's
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
- **Add a new page:** drop a new file in `pages/`, prefixed with a number so
  it sits in the right sidebar order (e.g. `5_📊_Progress.py`).

---

## ⚠️ Disclaimer

This is a study tool, not a religious authority. Recitation feedback and AI
answers can be imperfect — always verify important matters (especially fiqh
rulings) with a qualified scholar or a trusted mushaf/hadith collection.
