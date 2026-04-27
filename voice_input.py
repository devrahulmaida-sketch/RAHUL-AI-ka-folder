"""
core/voice_input.py
━━━━━━━━━━━━━━━━━━
Voice input engine.
Primary:  faster-whisper (offline, accurate, multilingual)
Fallback: SpeechRecognition + Google (online)

Runs in a background thread, calls on_text(text) when speech detected.
"""
from __future__ import annotations
import threading, queue, time
from typing import Callable

_listening   = threading.Event()
_stop_event  = threading.Event()
_result_q: queue.Queue = queue.Queue()


def start_listening(on_text: Callable[[str], None], ui=None):
    """
    Start background voice listener.
    on_text: called with transcribed text when speech detected.
    """
    _stop_event.clear()
    _listening.set()

    def _loop():
        if ui:
            ui.write_log("SYS: Voice input initializing…")

        # Try faster-whisper first (best offline STT)
        if _try_whisper(on_text, ui):
            return

        # Fallback: SpeechRecognition
        if _try_speech_recognition(on_text, ui):
            return

        if ui:
            ui.write_log("ERR: No STT engine available. Use typing.")

    threading.Thread(target=_loop, daemon=True).start()


def stop_listening():
    _stop_event.set()
    _listening.clear()


def _try_whisper(on_text: Callable, ui=None) -> bool:
    """faster-whisper: offline, accurate, supports Hindi."""
    try:
        from faster_whisper import WhisperModel
        import numpy as np
        import sounddevice as sd

        if ui:
            ui.write_log("SYS: Voice — using Whisper (offline)")

        # Use tiny model for speed, base for accuracy
        model = WhisperModel("base", device="cpu", compute_type="int8")
        SAMPLE_RATE = 16000
        CHUNK_SEC   = 4     # record 4 seconds at a time
        SILENCE_THR = 0.01  # silence threshold

        while not _stop_event.is_set():
            if not _listening.is_set():
                time.sleep(0.2)
                continue

            if ui:
                ui.set_state("LISTENING")

            # Record chunk
            audio = sd.rec(
                int(CHUNK_SEC * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="float32",
            )
            sd.wait()
            audio_flat = audio.flatten()

            # Skip if silence
            if np.abs(audio_flat).max() < SILENCE_THR:
                continue

            # Transcribe
            segments, info = model.transcribe(
                audio_flat,
                language=None,  # auto-detect Hindi + English
                beam_size=3,
                vad_filter=True,
            )
            text = " ".join(s.text for s in segments).strip()
            if text and len(text) > 2:
                if ui:
                    ui.write_log(f"You: {text}")
                on_text(text)

        return True

    except ImportError:
        return False
    except Exception as e:
        if ui:
            ui.write_log(f"ERR: Whisper failed: {e}")
        return False


def _try_speech_recognition(on_text: Callable, ui=None) -> bool:
    """SpeechRecognition fallback — uses Google STT (online)."""
    try:
        import speech_recognition as sr

        if ui:
            ui.write_log("SYS: Voice — using Google STT (online)")

        r   = sr.Recognizer()
        mic = sr.Microphone()

        r.energy_threshold        = 300
        r.dynamic_energy_threshold = True
        r.pause_threshold          = 0.8

        with mic as source:
            r.adjust_for_ambient_noise(source, duration=1)

        def _callback(recognizer, audio):
            if _stop_event.is_set():
                return
            try:
                # Try Hindi first, then English
                for lang in ["hi-IN", "en-IN", "en-US"]:
                    try:
                        text = recognizer.recognize_google(audio, language=lang)
                        if text:
                            if ui:
                                ui.write_log(f"You: {text}")
                            on_text(text)
                            return
                    except sr.UnknownValueError:
                        continue
            except Exception:
                pass

        stop_fn = r.listen_in_background(mic, _callback)

        # Wait until stop requested
        while not _stop_event.is_set():
            time.sleep(0.5)

        stop_fn(wait_for_stop=False)
        return True

    except ImportError:
        return False
    except Exception as e:
        if ui:
            ui.write_log(f"ERR: SpeechRecognition failed: {e}")
        return False


def is_whisper_available() -> bool:
    try:
        from faster_whisper import WhisperModel
        import sounddevice
        return True
    except ImportError:
        return False


def is_sr_available() -> bool:
    try:
        import speech_recognition
        import sounddevice
        return True
    except ImportError:
        return False
