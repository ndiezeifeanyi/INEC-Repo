"""
Automatic Speech Recognition (ASR) Engine (Phase 7).
Handles voter voice notes in Nigerian languages (English, Hausa, Yoruba, Igbo, Nigerian Pidgin).

Architectural & Licensing Guardrails:
1. Gated behind ENABLE_VOICE_ASR=False (default OFF).
2. Licence Audits:
   - OpenAI Whisper: MIT Licence (Permissive, commercial-friendly).
   - Meta MMS-ASR: CC-BY-NC 4.0 Licence (Non-commercial only; unsuitable for production deployments).
   - AfriHuBERT: Speech representation encoder, not an end-to-end ASR decoder.
3. Strict Privacy:
   - Audio bytes are processed strictly in memory and immediately discarded.
   - NEVER saved to disk, logged, or retained after transcription.
4. Fallback:
   - When ASR is disabled or audio is incomprehensible, returns polite text prompt in user's language.
"""

import io
import os
import wave
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

ENABLE_VOICE_ASR = os.environ.get("ENABLE_VOICE_ASR", "false").lower() in ("true", "1", "yes")

@dataclass
class ASRResult:
    success: bool
    transcript: str
    detected_language: Optional[str] = None
    confidence: float = 0.0
    error_message: Optional[str] = None

class SpeechRecognitionEngine:
    """
    Privacy-preserving voice note transcriber with licensing disclosures.
    """

    FALLBACK_PROMPTS = {
        "en": "I could not process the voice note. Please reply in text or try recording again.",
        "ha": "Ban sami damar jin sautin muryarka ba. Da fatan za a rubuto tambayarka a matsayin rubutu ko a sake daukar murya.",
        "yo": "Nko le gbo ohun ti o gba sile daadaa. E jowo fi iforukosile ranse tabi ki e ko oro na sinu leta.",
        "ig": "Enweghị m ike ịnụ ozi olu gị nke ọma. Biko zite ajụjụ gị na ederede ma ọ bụ detuo ya ọzọ.",
        "pcm": "I no fit hear your voice note clearly. Abeg type your question as text or try record am again."
    }

    def __init__(self, enabled: bool = ENABLE_VOICE_ASR):
        self.enabled = enabled

    def transcribe(self, audio_bytes: bytes, lang: str = "en") -> ASRResult:
        """
        Transcribes audio bytes strictly in memory, then immediately discards raw audio.
        """
        if not self.enabled:
            return ASRResult(
                success=False,
                transcript="",
                confidence=0.0,
                error_message="Voice transcription (ASR) is disabled by default in this environment."
            )

        if not audio_bytes or len(audio_bytes) < 44:  # minimum WAV header size
            return ASRResult(
                success=False,
                transcript="",
                confidence=0.0,
                error_message="Invalid or empty audio stream."
            )

        try:
            # Memory-only verification of WAV header
            with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                sample_rate = wf.getframerate()
                channels = wf.getnchannels()
                frames = wf.getnframes()
                logger.info(f"Received in-memory audio: {sample_rate}Hz, {channels}ch, {frames} frames. Discarding audio.")
        except Exception as e:
            return ASRResult(
                success=False,
                transcript="",
                confidence=0.0,
                error_message=f"Audio format decoding error: {e}"
            )
        finally:
            # Explicit in-memory dereferencing of audio bytes (H6 Privacy constraint)
            del audio_bytes

        # Production model inference placeholder (e.g. whisper-base or fine-tuned ASR)
        return ASRResult(
            success=False,
            transcript="",
            confidence=0.0,
            error_message="Local ASR model weights not configured; falling back to text prompt."
        )

    def get_fallback_message(self, lang: str = "en") -> str:
        return self.FALLBACK_PROMPTS.get(lang, self.FALLBACK_PROMPTS["en"])
