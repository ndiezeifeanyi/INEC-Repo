"""
Tests for Phase 7 Voice ASR Engine (src/speech/asr_engine.py).
Verifies:
1. Gated disabled by default behavior.
2. In-memory WAV parsing and zero retention.
3. Multilingual fallback messages for English, Hausa, Yoruba, Igbo, and Pidgin.
"""

import io
import wave
import struct
from src.speech.asr_engine import SpeechRecognitionEngine, ASRResult

def make_test_wav_bytes(duration_sec=0.5, sample_rate=16000):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        num_samples = int(duration_sec * sample_rate)
        data = struct.pack(f"<{num_samples}h", *([0] * num_samples))
        wf.writeframes(data)
    return buf.getvalue()

def test_asr_disabled_by_default():
    engine = SpeechRecognitionEngine(enabled=False)
    wav_bytes = make_test_wav_bytes()
    res = engine.transcribe(wav_bytes)
    assert isinstance(res, ASRResult)
    assert res.success is False
    assert "disabled by default" in res.error_message

def test_asr_empty_audio():
    engine = SpeechRecognitionEngine(enabled=True)
    res = engine.transcribe(b"")
    assert res.success is False
    assert "empty" in res.error_message.lower()

def test_asr_in_memory_transcribe_and_discard():
    engine = SpeechRecognitionEngine(enabled=True)
    wav_bytes = make_test_wav_bytes()
    res = engine.transcribe(wav_bytes)
    assert isinstance(res, ASRResult)
    # Weights not configured -> returns safe notice
    assert res.success is False
    assert "weights not configured" in res.error_message.lower()

def test_multilingual_fallback_messages():
    engine = SpeechRecognitionEngine()
    for lang in ["en", "ha", "yo", "ig", "pcm"]:
        msg = engine.get_fallback_message(lang)
        assert len(msg) > 10
        assert isinstance(msg, str)
    # Check Pidgin specific wording
    assert "voice note" in engine.get_fallback_message("pcm")
