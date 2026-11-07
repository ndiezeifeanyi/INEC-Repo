# System Card: INEC Multilingual Civic QA & Verifier

## 1. System Summary
- **System Name**: Independent Multilingual Electoral Rules & Verification Prototype
- **License**: MIT License
- **Target Context**: #AI4Elections Hackathon (Track 3)
- **Primary Function**:
  1. Retrieve verbatim legal clauses from the Electoral Act 2026 and INEC Guidelines 2026.
  2. Answer voter procedural questions in English, Hausa, Yoruba, and Igbo using deterministic legal templates.
  3. Verify website links and claims against an internal allowlist and a locally maintained database of known fraudulent links and published INEC bulletins.

---

## 2. Honest Limits & Failure Modes

1. **Generation is Template-Based, Not Neural**:
   - Natural language generation is performed by **deterministic Python templates** (`src/generation/prompt_builder.py`) wrapping retrieved statutory excerpts.
   - It cannot answer questions whose answers require synthesising across multiple complex unindexed legal precedents or case law.

2. **Glossary Unreviewed Status**:
   - **All entries in `data/glossaries/` are UNREVIEWED.**
   - While terms are drawn from common public civic terminology, no certified native-speaker linguist has officially validated them for this project.
   - Any term generated in Hausa, Yoruba, or Igbo must be treated as uncertified research draft text.

3. **Check Mode Does NOT Query Live Safe Browsing**:
   - URL verification uses an **internal domain allowlist** (`inecnigeria.org`, `cvr.inecnigeria.org`, `irev.inecnigeria.org`) and an internal blacklist of known malicious domains.
   - It **does not connect to Google Safe Browsing API**.
   - It defaults strictly to `"Can't tell"` for any message or claim not present in the local 3-bulletin corpus.

4. **Section 29A Amendment is UNCONFIRMED**:
   - The National Assembly pre-election amendment bill (proposed Section 29A) is **UNCONFIRMED**.
   - As of 2026-11-07, it does not appear in Official Gazette No. 40 (Act No. 1, 2026). The system explicitly states that presidential assent is unconfirmed and directs voters to the Official Gazette.

5. **Audio Synthesis is Synthetic Offline Tones**:
   - `src/speech/tts_engine.py` generates synthetic PCM sine wave tones in offline mode to demonstrate low-bandwidth audio delivery (<25 KB).
   - Real voice synthesis requires loading external Meta MMS-TTS checkpoint weights, governed by non-commercial license CC-BY-NC-4.0.

6. **Retrieval Performance & Circularity Disclosure**:
   - On the 20-question statutory set where query phrases map to indexed terms, Recall@3 is **95.0%**.
   - On the held-out unaligned set (n=8), Recall@3 drops to **37.5%** [95% CI: 4.0% - 71.0%], demonstrating that performance degrades when voter phrasing deviates from the translation dictionary.

7. **Zero Live INEC Access**:
   - Does not touch live INEC voter registration databases, polling unit collation hardware, or IReV servers.
