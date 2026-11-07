# ADR 0002: Text-to-Speech Engine and Licensing Restrictions

- **Status**: Accepted
- **Date**: 2026-11-07
- **Context**: Need to provide accessible audio responses for voters with low literacy in Hausa, Yoruba, and Igbo.

## Decision

We select Meta's Massively Multilingual Speech (MMS) TTS models:
- Hausa: `facebook/mms-tts-hau`
- Yoruba: `facebook/mms-tts-yor`
- Igbo: `facebook/mms-tts-ibo`

### Licensing Compliance & Restrictions [VERIFIED]
1. **License**: Creative Commons Attribution-NonCommercial 4.0 International (`CC-BY-NC-4.0`).
2. **Commercial Restriction**: Cannot be monetized, packaged into paid products, or deployed in commercial services without an explicit commercial license from Meta.
3. **Hackathon & Research Scope**: Permitted for non-commercial civic education, hackathon demonstration, and academic evaluation.
4. **Attribution**: The system UI and System Card must display:
   > *"Audio playback generated using Meta MMS-TTS models under CC-BY-NC-4.0 for non-commercial voter education research."*
5. **Alternative for Commercial Production**: If commercialized, replace with commercial-ready speech APIs (e.g. Google Cloud Text-to-Speech or fine-tuned Piper TTS models under Apache 2.0 / MIT).

## Audio Compression Strategy
To accommodate Nigeria's low-bandwidth mobile networks, raw PCM wave outputs are compressed to Opus/OGG at 16 kbps mono, producing audio clips under 25 KB for typical 30-second explanations.

