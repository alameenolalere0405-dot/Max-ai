"""
MAX AI — Vision Engine
LEREON Technologies

Screenshot capture, OCR text extraction, image analysis via AI vision APIs.
Hand tracking / gesture recognition via OpenCV + MediaPipe (optional).
Camera access requires explicit permission.
"""

import logging
import asyncio
import base64
import io
import time
from pathlib import Path
from typing import Optional, Callable

logger = logging.getLogger("MAX.vision")
ROOT = Path(__file__).parent.parent
UPLOAD_DIR = ROOT / "uploads"


class VisionEngine:
    """
    Handles all visual intelligence for MAX AI:
    - Screenshot capture and analysis
    - Image loading and analysis
    - OCR (text extraction from images)
    - Camera frame capture (permission-gated)
    - Hand/gesture detection (requires opencv-python + mediapipe)
    """

    def __init__(self, config=None):
        self.config = config
        self._camera = None
        self._gesture_active = False
        self._gesture_callback: Optional[Callable[[str], None]] = None
        UPLOAD_DIR.mkdir(exist_ok=True)
        logger.info("Vision engine initialized.")

    # ── Screenshot ────────────────────────────────────────────────────────

    async def capture_screenshot(self, monitor: int = 1) -> Optional[str]:
        """
        Capture a screenshot and save it.
        Returns file path or None on failure.
        """
        if self.config and not self.config.permission("screen_capture"):
            logger.warning("Screenshot permission denied.")
            return None

        filename = UPLOAD_DIR / f"screenshot_{int(time.time())}.png"
        try:
            import mss
            import mss.tools
            with mss.mss() as sct:
                monitors = sct.monitors
                idx = min(monitor, len(monitors) - 1)
                img = sct.grab(monitors[idx])
                mss.tools.to_png(img.rgb, img.size, output=str(filename))
            logger.info(f"Screenshot: {filename}")
            return str(filename)
        except ImportError:
            pass
        # PIL fallback
        try:
            from PIL import ImageGrab
            img = await asyncio.to_thread(ImageGrab.grab)
            await asyncio.to_thread(img.save, str(filename))
            return str(filename)
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return None

    # ── Image → Base64 ────────────────────────────────────────────────────

    def image_to_base64(self, image_path: str) -> Optional[str]:
        """Load an image file and return base64-encoded string."""
        try:
            path = Path(image_path)
            if not path.exists():
                return None
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            logger.error(f"image_to_base64 error: {e}")
            return None

    def pil_image_to_base64(self, pil_image) -> str:
        """Convert a PIL Image object to base64 PNG string."""
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    # ── OCR ───────────────────────────────────────────────────────────────

    async def extract_text_ocr(self, image_path: str) -> str:
        """
        Extract text from an image using pytesseract OCR.
        Requires: pip install pytesseract Pillow
        And Tesseract-OCR installed on the system.
        """
        try:
            import pytesseract
            from PIL import Image
            img = await asyncio.to_thread(Image.open, image_path)
            text = await asyncio.to_thread(pytesseract.image_to_string, img)
            return text.strip() or "(No text detected)"
        except ImportError:
            return "OCR not available. Install: pip install pytesseract\nAnd Tesseract-OCR from https://github.com/UB-Mannheim/tesseract/wiki"
        except Exception as e:
            return f"OCR error: {e}"

    # ── AI Vision Analysis ────────────────────────────────────────────────

    async def analyze_image_with_ai(
        self,
        image_path: str,
        question: str = "Describe this image in detail.",
        provider=None,
    ) -> str:
        """
        Send an image to an AI vision model for analysis.
        Supports OpenAI GPT-4V and Anthropic Claude Vision.
        """
        b64 = self.image_to_base64(image_path)
        if not b64:
            return f"Could not load image: {image_path}"

        suffix = Path(image_path).suffix.lower()
        mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".png": "image/png", ".gif": "image/gif",
                    ".webp": "image/webp"}
        mime = mime_map.get(suffix, "image/png")

        if provider is None:
            return "No AI provider available for vision analysis."

        pname = getattr(provider, "name", "")

        # OpenAI / OpenRouter / DeepSeek compatible
        if pname in ("openai", "openrouter", "deepseek"):
            return await self._analyze_openai(provider, b64, mime, question)

        # Anthropic Claude
        if pname == "anthropic":
            return await self._analyze_anthropic(provider, b64, mime, question)

        # Gemini
        if pname == "gemini":
            return await self._analyze_gemini(provider, image_path, question)

        return f"Vision analysis not supported for provider: {pname}"

    async def _analyze_openai(self, provider, b64: str, mime: str, question: str) -> str:
        try:
            client = provider._client_obj()
            resp = await client.chat.completions.create(
                model=provider.model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image_url",
                         "image_url": {"url": f"data:{mime};base64,{b64}"}},
                        {"type": "text", "text": question}
                    ]
                }],
                max_tokens=1024,
            )
            return resp.choices[0].message.content or "(No response)"
        except Exception as e:
            return f"OpenAI vision error: {e}"

    async def _analyze_anthropic(self, provider, b64: str, mime: str, question: str) -> str:
        try:
            client = provider._client_obj()
            resp = await client.messages.create(
                model=provider.model,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image",
                         "source": {"type": "base64", "media_type": mime, "data": b64}},
                        {"type": "text", "text": question}
                    ]
                }]
            )
            return resp.content[0].text if resp.content else "(No response)"
        except Exception as e:
            return f"Anthropic vision error: {e}"

    async def _analyze_gemini(self, provider, image_path: str, question: str) -> str:
        try:
            import google.generativeai as genai
            genai.configure(api_key=provider._api_key)
            model = genai.GenerativeModel("gemini-1.5-pro")
            from PIL import Image
            img = Image.open(image_path)
            response = await asyncio.to_thread(model.generate_content, [question, img])
            return response.text
        except Exception as e:
            return f"Gemini vision error: {e}"

    # ── Camera ────────────────────────────────────────────────────────────

    async def capture_camera_frame(self) -> Optional[str]:
        """
        Capture a single frame from the webcam.
        Requires explicit camera permission.
        """
        if self.config and not self.config.permission("camera"):
            return None
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return None
            ret, frame = await asyncio.to_thread(cap.read)
            cap.release()
            if not ret:
                return None
            filename = UPLOAD_DIR / f"camera_{int(time.time())}.png"
            await asyncio.to_thread(cv2.imwrite, str(filename), frame)
            return str(filename)
        except ImportError:
            logger.warning("opencv-python not installed. Camera unavailable.")
            return None
        except Exception as e:
            logger.error(f"Camera capture error: {e}")
            return None

    # ── Hand Tracking / Gesture Control ──────────────────────────────────

    def start_gesture_control(self, callback: Callable[[str], None]) -> bool:
        """
        Start real-time hand gesture detection.
        Requires: pip install opencv-python mediapipe
        Camera permission required.
        Returns True if started, False if unavailable.
        """
        if self.config and not self.config.permission("camera"):
            logger.warning("Gesture control: camera permission denied.")
            return False

        try:
            import cv2
            import mediapipe as mp
        except ImportError:
            logger.warning("Gesture control unavailable: install opencv-python mediapipe")
            return False

        self._gesture_callback = callback
        self._gesture_active = True

        import threading
        t = threading.Thread(target=self._gesture_loop, daemon=True, name="MAX-Gesture")
        t.start()
        logger.info("Gesture control started.")
        return True

    def stop_gesture_control(self):
        self._gesture_active = False
        if self._camera:
            try:
                self._camera.release()
            except Exception:
                pass
        logger.info("Gesture control stopped.")

    def _gesture_loop(self):
        """Background loop: detect hand gestures and fire callbacks."""
        try:
            import cv2
            import mediapipe as mp
        except ImportError as e:
            logger.warning(f"Gesture control unavailable: {e}")
            self._gesture_active = False
            return

        # Verify mediapipe has the solutions API (older versions may not)
        if not hasattr(mp, "solutions") or not hasattr(mp.solutions, "hands"):
            logger.warning(
                "mediapipe.solutions not available in this version. "
                "Install: pip install mediapipe>=0.10"
            )
            self._gesture_active = False
            return

        try:
            mp_hands = mp.solutions.hands
            cap = cv2.VideoCapture(0)
            self._camera = cap

            if not cap.isOpened():
                logger.warning("Gesture control: could not open camera.")
                self._gesture_active = False
                return

            with mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=2,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.5
            ) as hands:
                while self._gesture_active:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = hands.process(rgb)
                    if results.multi_hand_landmarks:
                        for landmarks in results.multi_hand_landmarks:
                            gesture = self._classify_gesture(landmarks)
                            if gesture and self._gesture_callback:
                                self._gesture_callback(gesture)
                    time.sleep(0.1)
            cap.release()
        except Exception as e:
            logger.error(f"Gesture loop error: {e}")
        finally:
            self._gesture_active = False

    def _classify_gesture(self, landmarks) -> Optional[str]:
        """
        Classify a hand gesture from MediaPipe landmarks.
        Returns gesture name or None.
        """
        try:
            lm = landmarks.landmark

            # Key landmark indices (MediaPipe hand)
            # 4=thumb tip, 8=index tip, 12=middle tip, 16=ring tip, 20=pinky tip
            # 3=thumb ip, 6=index pip, 10=mid pip, 14=ring pip, 18=pinky pip

            def finger_up(tip_idx, pip_idx):
                return lm[tip_idx].y < lm[pip_idx].y  # tip higher = finger up

            thumb_up  = lm[4].x < lm[3].x  # thumb tip left of thumb ip (right hand)
            index_up  = finger_up(8, 6)
            middle_up = finger_up(12, 10)
            ring_up   = finger_up(16, 14)
            pinky_up  = finger_up(20, 18)

            fingers_up = sum([index_up, middle_up, ring_up, pinky_up])

            # Open palm: all 4 fingers up
            if fingers_up == 4:
                return "open_palm"

            # Thumbs up: only thumb up, rest down
            if thumb_up and fingers_up == 0:
                return "thumbs_up"

            # Point: only index finger up
            if index_up and not middle_up and not ring_up and not pinky_up:
                return "point"

            # Peace / V-sign: index + middle up
            if index_up and middle_up and not ring_up and not pinky_up:
                return "peace"

            # Fist: no fingers up
            if fingers_up == 0 and not thumb_up:
                return "fist"

            return None
        except Exception:
            return None

    # ── Image resize utility ──────────────────────────────────────────────

    async def resize_for_api(self, image_path: str, max_dim: int = 1024) -> str:
        """Resize an image to fit within max_dim x max_dim for API calls."""
        try:
            from PIL import Image
            img = Image.open(image_path)
            img.thumbnail((max_dim, max_dim), Image.LANCZOS)
            out = Path(image_path).with_suffix(".resized.png")
            img.save(str(out), "PNG")
            return str(out)
        except Exception as e:
            logger.warning(f"resize_for_api error: {e}")
            return image_path
