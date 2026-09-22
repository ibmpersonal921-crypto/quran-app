"""
services/live_stream_coach.py
-------------------------------
TRUE continuous live correction — this is the "at any cost" version.

What this unlocks vs. the free Live Mode (Web Speech API in recitation_coach.py):
  - Continuous WebRTC mic streaming (streamlit-webrtc) instead of the
    browser's own start/stop recognition sessions -> far more stable.
  - Deepgram's streaming transcription (paid, cheap, generous free trial
    credit) instead of the free/unofficial browser API -> works in every
    browser (not just Chrome/Edge), much lower latency, more accurate.

What money still does NOT buy: a model that judges tajweed (correct
makhraj/articulation points, madd length, qalqalah, etc.) the way a human
teacher does. Every option here — free or paid — is "accurate live word
matching," not "an AI tajweed examiner." That system doesn't exist
off-the-shelf at any price; it would need a custom model trained on
tajweed-annotated audio, which is a research project of its own.

Setup: pip install streamlit-webrtc deepgram-sdk streamlit-autorefresh av numpy
       Get a free-trial key at https://console.deepgram.com (paid after trial
       credit runs out — a few dollars covers a lot of practice minutes).

Honesty note: this file wires together three moving parts (WebRTC audio
threading, a persistent websocket, and a polling UI refresh) that I cannot
run end-to-end in a browser from here to verify. It follows the documented,
standard pattern for each library, but test it locally before you rely on
it — if something breaks, the free Live Mode / Practice Mode in
recitation_coach.py are the tested fallbacks.
"""

from __future__ import annotations

import os
import queue
import threading

import numpy as np
import streamlit as st

from utils.helpers import normalize_arabic

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")


def is_configured() -> bool:
    return bool(DEEPGRAM_API_KEY)


class _LiveSession:
    """One persistent Deepgram connection + the state a background thread
    writes into and the main Streamlit script reads back out of."""

    def __init__(self, reference_arabic: str):
        self.audio_queue: "queue.Queue[bytes]" = queue.Queue()
        self.transcript_parts: list[str] = []
        self.lock = threading.Lock()
        self.ref_words = normalize_arabic(reference_arabic).split()
        self.matched = [False] * len(self.ref_words)
        self.ref_index = 0
        self.connected = False
        self.error = None
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()

    def push_audio(self, pcm16_bytes: bytes):
        self.audio_queue.put(pcm16_bytes)

    def _on_final_transcript(self, text: str):
        said = normalize_arabic(text).split()
        with self.lock:
            for word in said:
                if self.ref_index >= len(self.ref_words):
                    break
                if word == self.ref_words[self.ref_index]:
                    self.matched[self.ref_index] = True
                self.ref_index += 1
            self.transcript_parts.append(text)

    def _run(self):
        try:
            from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

            dg = DeepgramClient(DEEPGRAM_API_KEY)
            conn = dg.listen.live.v("1")

            def on_message(_self, result, **_kwargs):
                try:
                    sentence = result.channel.alternatives[0].transcript
                except Exception:
                    return
                if sentence and getattr(result, "is_final", True):
                    self._on_final_transcript(sentence)

            def on_error(_self, error, **_kwargs):
                self.error = str(error)

            conn.on(LiveTranscriptionEvents.Transcript, on_message)
            conn.on(LiveTranscriptionEvents.Error, on_error)

            options = LiveOptions(
                model="nova-2",
                language="ar",
                encoding="linear16",
                channels=1,
                sample_rate=16000,
                interim_results=True,
                punctuate=False,
            )
            if not conn.start(options):
                self.error = "Could not open Deepgram connection — check DEEPGRAM_API_KEY."
                return
            self.connected = True

            while not self._stop.is_set():
                try:
                    chunk = self.audio_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                conn.send(chunk)

            conn.finish()
        except Exception as e:  # noqa: BLE001
            self.error = str(e)


def get_or_create_session(session_key: str, reference_arabic: str) -> _LiveSession:
    if session_key not in st.session_state:
        session = _LiveSession(reference_arabic)
        session.start()
        st.session_state[session_key] = session
    return st.session_state[session_key]


def audio_frame_to_pcm16(frame) -> bytes:
    """
    Convert an av.AudioFrame (as delivered by streamlit-webrtc, typically
    48kHz stereo/mono float or int) to 16kHz mono PCM16 bytes, the format
    Deepgram's linear16 encoding expects.
    """
    arr = frame.to_ndarray()
    if arr.ndim == 2:  # (channels, samples) -> mono by averaging channels
        arr = arr.mean(axis=0)
    arr = arr.astype(np.float32)
    if arr.max() > 1.0 or arr.min() < -1.0:
        arr = arr / 32768.0  # already int16-range -> normalize to [-1, 1]

    src_rate = frame.sample_rate or 48000
    target_rate = 16000
    if src_rate != target_rate:
        duration = len(arr) / src_rate
        target_len = int(duration * target_rate)
        arr = np.interp(
            np.linspace(0, len(arr), target_len, endpoint=False),
            np.arange(len(arr)),
            arr,
        )
    pcm16 = np.clip(arr * 32767, -32768, 32767).astype(np.int16)
    return pcm16.tobytes()


def build_word_spans_html(session: "_LiveSession") -> str:
    with session.lock:
        ref_words = session.ref_words
        matched = list(session.matched)
        ref_index = session.ref_index
    spans = []
    for i, w in enumerate(ref_words):
        if matched[i]:
            cls = "qsc-word-correct"
        elif i < ref_index:
            cls = "qsc-word-wrong"
        else:
            cls = ""
        spans.append(f'<span class="qsc-word {cls}">{w}</span>')
    return "".join(spans)
