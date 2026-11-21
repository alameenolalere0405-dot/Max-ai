"""
MAX AI — Voice Engine
Handles: STT (SpeechRecognition / Whisper), TTS (pyttsx3), wake word detection.
All audio access is permission-gated and stoppable.
"""

import logging
import threading
import queue
import time
from typing import Callable, Optional

logger = logging.getLogger("MAX.voice")


class VoiceEngine:
    """
    Manages speech-to-text and text-to-speech for MAX AI.
    Designed to run in background threads and emit callbacks.
    """

    def __init__(self, config):
        self.config = config
        self._tts_engine = None
        self._recognizer = None
        self._microphone = None
        self._listening = False
        self._tts_lock = threading.Lock()
        self._wake_active = False
        self._stop_event = threading.Event()
        self._tts_queue: queue.Queue = queue.Queue()
        self._tts_thread: Optional[threading.Thread] = None

        # Callbacks
        self.on_transcript: Optional[Callable[[str], None]] = None
        self.on_wake_word: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_listening_state: Optional[Callable[[bool], None]] = None

        self._init_tts()

    # ── TTS ──────────────────────────────────────────────────────────────

    def _init_tts(self):
        try:
            import pyttsx3
            self._tts_engine = pyttsx3.init()
            rate = self._tts_engine.getProperty("rate")
            self._tts_engine.setProperty("rate", max(150, rate - 20))
            # Start TTS worker thread
            self._tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
            self._tts_thread.start()
            logger.info("TTS engine initialized (pyttsx3).")
        except Exception as e:
            logger.warning(f"TTS init failed: {e}")

    def _tts_worker(self):
        """Drain the TTS queue in a dedicated thread."""
        while not self._stop_event.is_set():
            try:
                text = self._tts_queue.get(timeout=0.5)
                if text is None:
                    break
                with self._tts_lock:
                    if self._tts_engine:
                        try:
                            self._tts_engine.say(text)
                            self._tts_engine.runAndWait()
                        except Exception as e:
                            logger.warning(f"TTS speak error: {e}")
            except queue.Empty:
                continue

    def speak(self, text: str):
        """Queue text to be spoken aloud."""
        if not self.config.voice_output_enabled:
            return
        if not text or not text.strip():
            return
        # Clip very long responses
        words = text.split()
        if len(words) > 200:
            text = " ".join(words[:200]) + "... (truncated)"
        self._tts_queue.put(text)

    def stop_speaking(self):
        """Interrupt current speech."""
        with self._tts_lock:
            if self._tts_engine:
                try:
                    self._tts_engine.stop()
                except Exception:
                    pass
        # Drain queue
        while not self._tts_queue.empty():
            try:
                self._tts_queue.get_nowait()
            except queue.Empty:
                break

    # ── STT ──────────────────────────────────────────────────────────────

    def _init_recognizer(self):
        if self._recognizer is None:
            try:
                import speech_recognition as sr
                self._recognizer = sr.Recognizer()
                self._recognizer.pause_threshold = 0.8
                self._recognizer.energy_threshold = 300
                self._microphone = sr.Microphone()
                logger.info("STT recognizer initialized (SpeechRecognition).")
            except ImportError:
                logger.warning("SpeechRecognition not installed.")
            except Exception as e:
                logger.warning(f"STT init failed: {e}")

    def listen_once(self) -> Optional[str]:
        """
        Block and listen for one utterance.
        Returns transcribed text or None on failure.
        """
        self._init_recognizer()
        if not self._recognizer or not self._microphone:
            if self.on_error:
                self.on_error("Microphone not available. Install pyaudio and SpeechRecognition.")
            return None
        try:
            import speech_recognition as sr
            if self.on_listening_state:
                self.on_listening_state(True)
            with self._microphone as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self._recognizer.listen(source, timeout=10, phrase_time_limit=30)
            if self.on_listening_state:
                self.on_listening_state(False)
            # Try Google STT first (free, no key)
            try:
                text = self._recognizer.recognize_google(audio, language="en-US")
                return text
            except sr.UnknownValueError:
                return None
            except sr.RequestError:
                # Fallback: try Whisper if installed
                return self._whisper_fallback(audio)
        except Exception as e:
            if self.on_listening_state:
                self.on_listening_state(False)
            logger.error(f"listen_once error: {e}")
            if self.on_error:
                self.on_error(str(e))
            return None

    def _whisper_fallback(self, audio) -> Optional[str]:
        try:
            import whisper
            import tempfile, os
            wav_data = audio.get_wav_data()
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(wav_data)
                tmp = f.name
            model = whisper.load_model("base")
            result = model.transcribe(tmp)
            os.unlink(tmp)
            return result.get("text", "").strip() or None
        except ImportError:
            logger.warning("openai-whisper not installed; fallback unavailable.")
        except Exception as e:
            logger.warning(f"Whisper fallback failed: {e}")
        return None

    # ── Continuous listening ──────────────────────────────────────────────

    def start_continuous_listen(self, callback: Callable[[str], None]):
        """Start a background thread that continuously listens and fires callback."""
        self.on_transcript = callback
        self._listening = True
        t = threading.Thread(target=self._continuous_loop, daemon=True)
        t.start()

    def stop_continuous_listen(self):
        self._listening = False
        if self.on_listening_state:
            self.on_listening_state(False)

    def _continuous_loop(self):
        self._init_recognizer()
        if not self._recognizer or not self._microphone:
            logger.warning("Cannot start continuous listen: no microphone.")
            return
        import speech_recognition as sr
        logger.info("Continuous listen loop started.")
        while self._listening and not self._stop_event.is_set():
            transcript = self.listen_once()
            if transcript and self.on_transcript:
                self.on_transcript(transcript)
            time.sleep(0.1)
        logger.info("Continuous listen loop stopped.")

    # ── Wake word ─────────────────────────────────────────────────────────

    def start_wake_word(self, callback: Callable[[], None]):
        """
        Start wake word detection using Picovoice Porcupine if available,
        otherwise fall back to keyword spotting via SpeechRecognition.
        """
        self.on_wake_word = callback
        self._wake_active = True
        t = threading.Thread(target=self._wake_loop, daemon=True)
        t.start()
        logger.info("Wake word detection started.")

    def stop_wake_word(self):
        self._wake_active = False
        logger.info("Wake word detection stopped.")

    def _wake_loop(self):
        # Try Picovoice Porcupine
        picovoice_key = self.config.get("assistant", "picovoice_key", default="")
        if picovoice_key:
            self._porcupine_wake_loop(picovoice_key)
            return
        # Fallback: keyword spotting
        self._keyword_wake_loop()

    def _porcupine_wake_loop(self, access_key: str):
        try:
            import pvporcupine
            import pyaudio
            porcupine = pvporcupine.create(
                access_key=access_key,
                keywords=["hey google"]  # Closest available free keyword
            )
            pa = pyaudio.PyAudio()
            stream = pa.open(
                rate=porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=porcupine.frame_length
            )
            logger.info("Porcupine wake word active.")
            while self._wake_active:
                pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
                import struct
                pcm_data = struct.unpack_from("h" * porcupine.frame_length, pcm)
                index = porcupine.process(pcm_data)
                if index >= 0:
                    logger.info("Wake word detected!")
                    if self.on_wake_word:
                        self.on_wake_word()
            stream.stop_stream()
            stream.close()
            pa.terminate()
            porcupine.delete()
        except ImportError:
            logger.warning("pvporcupine not installed — using keyword fallback.")
            self._keyword_wake_loop()
        except Exception as e:
            logger.error(f"Porcupine error: {e} — using keyword fallback.")
            self._keyword_wake_loop()

    def _keyword_wake_loop(self):
        """Simple keyword-matching fallback wake word."""
        logger.info("Wake word: keyword-matching mode (say 'hey max').")
        self._init_recognizer()
        if not self._recognizer or not self._microphone:
            logger.warning("Cannot start wake word: no microphone available.")
            return
        import speech_recognition as sr
        while self._wake_active:
            try:
                with self._microphone as source:
                    audio = self._recognizer.listen(source, timeout=5, phrase_time_limit=5)
                text = self._recognizer.recognize_google(audio, language="en-US").lower()
                if "hey max" in text or "hey, max" in text:
                    logger.info("Wake word: 'Hey MAX' detected.")
                    if self.on_wake_word:
                        self.on_wake_word()
            except Exception:
                pass
            time.sleep(0.05)

    # ── Shutdown ──────────────────────────────────────────────────────────

    def shutdown(self):
        self._stop_event.set()
        self._listening = False
        self._wake_active = False
        self.stop_speaking()
        self._tts_queue.put(None)  # Signal TTS worker to stop
        logger.info("Voice engine shut down.")
