# ADR 0007: Voice Note ASR/TTS Architecture and Licensing Guardrails

- **Status**: Accepted (Implemented in Phase 7)
- **Date**: 2026-11-08
- **Scope**: Voter voice note ingestion (ASR) and speech audio synthesis (TTS) for civic engagement in English, Hausa, Yoruba, Igbo, and Nigerian Pidgin.

---

## 1. Context and Problem Statement

A substantial segment of Nigerian voters, particularly those with low literacy or visual impairments, rely on WhatsApp voice notes.

However, voice processing presents significant compliance, licensing, and privacy risks:
1. **Licensing Obstacles**:
   - Meta's **MMS-ASR** and **MMS-TTS** models are released under **CC-BY-NC 4.0** (Creative Commons Attribution-NonCommercial). Distributing non-commercial weights in a solution that may transition into commercial or partner use violates licensing terms.
   - **AfriHuBERT** is a self-supervised speech representation encoder, NOT an off-the-shelf ASR decoder.
   - **OpenAI Whisper** models are released under the permissive **MIT Licence**, but lack native high-accuracy fine-tuning for low-resource Nigerian languages without supplemental civic speech datasets.
2. **Privacy Violations (Hard Constraint H6)**:
   - Voice notes contain identifiable biometric speaker characteristics (voiceprints). Retaining or logging audio recordings creates catastrophic data-privacy risks under the Nigeria Data Protection Act (NDPA 2023).

---

## 2. Decision and Architecture

### 2.1 Safe Gating and Defaults
- `ENABLE_VOICE_ASR` defaults to `False`.
- `ENABLE_VOICE_TTS` defaults to `False`.
- The system operates 100% reliably in text mode without any external audio dependencies.

### 2.2 Strict Zero-Retention Audio Processing (Constraint H6)
- Any incoming voice note is processed strictly **in-memory**.
- Audio bytes are converted to 16kHz mono WAV in a transient `io.BytesIO` buffer.
- Immediately upon transcription (or upon failure), raw audio bytes are explicitly deleted and memory dereferenced.
- **Never saved to disk, never stored in session caches, and never logged.**

### 2.3 Respectful Multilingual Fallback Prompts
When voice ASR is disabled or cannot decipher audio, the system sends an immediate localized prompt:
- **English**: *"I could not process the voice note. Please reply in text or try recording again."*
- **Hausa**: *"Ban sami damar jin sautin muryarka ba. Da fatan za a rubuto tambayarka a matsayin rubutu ko a sake daukar murya."*
- **Yoruba**: *"Nko le gbo ohun ti o gba sile daadaa. E jowo fi iforukosile ranse tabi ki e ko oro na sinu leta."*
- **Igbo**: *"Enweghị m ike ịnụ ozi olu gị nke ọma. Biko zite ajụjụ gị na ederede ma ọ bụ detuo ya ọzọ."*
- **Pidgin**: *"I no fit hear your voice note clearly. Abeg type your question as text or try record am again."*

### 2.4 TTS Licensing Guardrail
- `MMSTTSEngine` produces lightweight test tones to test bandwidth and audio transport without embedding CC-BY-NC 4.0 binaries.
- All audio responses carry the explicit header:
  `X-License: Audio test tone only (synthetic PCM tone generator)`.
