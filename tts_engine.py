"""
core/tts_engine.py
━━━━━━━━━━━━━━━━━
Text-to-Speech engine — Indian male voice.
Primary:  edge-tts  (Microsoft Neural TTS, free, needs internet)
Fallback: pyttsx3   (offline, system TTS)

Indian male voices:
  edge-tts: hi-IN-MadhurNeural (Hindi), en-IN-PrabhatNeural (English)
"""
from __future__ import annotations
import asyncio, os, threading, tempfile, time, re
from pathlib import Path

# ── Voice preference ──────────────────────────────────────────────────────────
EDGE_VOICES = [
    "hi-IN-MadhurNeural",    # Hindi Indian Male (primary)
    "en-IN-PrabhatNeural",   # English Indian Male (fallback)
    "en-IN-NeerjaNeural",    # English Indian Female (last resort)
]

_tts_lock  = threading.Lock()
_stop_flag = threading.Event()
_current_proc = None


def _clean_for_tts(text: str) -> str:
    """Remove markdown, symbols, and extra whitespace before TTS."""
    text = re.sub(r'\*+', '', text)           # bold/italic
    text = re.sub(r'`+[^`]*`+', '', text)     # code blocks
    text = re.sub(r'#+\s*', '', text)          # headings
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # links
    text = re.sub(r'[◈◇▸▶●○⚡✓✗✱]', '', text) # UI symbols
    text = re.sub(r'SYS:\s*', '', text)        # log prefixes
    text = re.sub(r'ERR:\s*', 'Error: ', text)
    text = text.replace('RAHUL:', '').replace('You:', '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:800]   # cap length to avoid very long TTS


def speak(text: str, blocking: bool = False):
    """Speak text in background thread (non-blocking by default)."""
    clean = _clean_for_tts(text)
    if not clean or len(clean) < 3:
        return

    def _run():
        global _current_proc
        with _tts_lock:
            _stop_flag.clear()
            success = _speak_edge(clean)
            if not success:
                _speak_pyttsx3(clean)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    if blocking:
        t.join()


def stop():
    """Stop current TTS playback."""
    global _current_proc
    _stop_flag.set()
    if _current_proc:
        try:
            _current_proc.terminate()
        except Exception:
            pass


def _speak_edge(text: str) -> bool:
    """edge-tts: Microsoft Neural TTS — best quality Indian male voice."""
    try:
        import edge_tts, subprocess, sys

        # Try voices in priority order
        for voice in EDGE_VOICES:
            try:
                tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                tmp.close()
                tmp_path = tmp.name

                # Generate audio
                async def _gen():
                    comm = edge_tts.Communicate(text, voice)
                    await comm.save(tmp_path)

                asyncio.run(_gen())

                if not Path(tmp_path).exists() or Path(tmp_path).stat().st_size < 100:
                    continue

                # Play audio
                global _current_proc
                if sys.platform == "win32":
                    _current_proc = subprocess.Popen(
                        ["powershell", "-c", f"(New-Object Media.SoundPlayer '{tmp_path}').PlaySync()"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
                else:
                    for player in ["mpg123", "mpg321", "ffplay", "vlc"]:
                        if os.system(f"which {player} > /dev/null 2>&1") == 0:
                            _current_proc = subprocess.Popen(
                                [player, "-q", tmp_path] if player != "ffplay"
                                else ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", tmp_path],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            )
                            break

                if _current_proc:
                    _current_proc.wait()

                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

                return True

            except Exception:
                continue

    except ImportError:
        pass
    return False


def _speak_pyttsx3(text: str) -> bool:
    """pyttsx3 fallback — offline system TTS."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 165)
        engine.setProperty("volume", 0.95)

        # Try to find Indian male voice
        voices = engine.getProperty("voices")
        for v in voices:
            name = (v.name or "").lower()
            if any(kw in name for kw in ["india", "hindi", "prabhat", "ravi"]):
                engine.setProperty("voice", v.id)
                break

        engine.say(text)
        engine.runAndWait()
        return True
    except Exception:
        return False


def is_edge_tts_available() -> bool:
    try:
        import edge_tts
        return True
    except ImportError:
        return False


def is_pyttsx3_available() -> bool:
    try:
        import pyttsx3
        return True
    except ImportError:
        return False
