# System Card: INEC Multilingual Civic QA & Verifier

## 1. System Summary
- **System Name**: Independent Multilingual Electoral Rules & Verification Prototype
- **License**: MIT License
- **Target Context**: #AI4Elections Hackathon (Track 3: Inclusive and Multilingual Civic Tech)
- **Primary Function**:
  1. Retrieve verbatim legal clauses from the Electoral Act 2026 and official INEC electronic transmission procedure.
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
   - All refusal strings across English, Hausa, Yoruba, and Igbo are UNREVIEWED and listed in `data/glossaries/refusals_unreviewed.json` for native audit.

3. **Check Mode Does NOT Query Live Safe Browsing**:
   - URL verification uses an **internal domain allowlist** (`inecnigeria.org`, `cvr.inecnigeria.org`, `irev.inecnigeria.org`) and an internal blacklist of known malicious domains (`linksnapro.com`, `pvc-inecnigeria-org.blogspot.com`).
   - It **does not connect to Google Safe Browsing API**.
   - It defaults strictly to `"Can't tell"` for any message or claim not present in the local 3-bulletin corpus.
   - Does not evaluate whether political claims or opinions are True or False.

4. **Section 29A Amendment is UNCONFIRMED**:
   - The National Assembly pre-election amendment bill (proposed Section 29A) is **UNCONFIRMED**.
   - As of 2026-11-07, it does not appear in Official Gazette No. 40 (Act No. 1, 2026). The notice is maintained in application configuration (`src/config.py`) and is strictly excluded from the statutory corpus (`data/processed/electoral_act_2026.jsonl`).
   - When queried, the system explicitly states: *"Passed by both chambers (Apr/May 2026); I could not confirm presidential assent as of 2026-11-07; check the Gazette."*

5. **Audio is Test Tone Only**:
   - `src/speech/tts_engine.py` generates offline synthetic PCM sine wave tones (`<25 KB`) solely to test the browser audio playback pipeline without external network dependencies.
   - Production neural voice synthesis requires loading external Meta MMS-TTS checkpoint weights, governed by non-commercial license CC-BY-NC-4.0.

6. **Retrieval Performance & Circularity Disclosure**:
   - On the 20-question statutory set where query phrases map to indexed terms, Path B achieves Recall@3 of **90.0%** and MRR of **0.639**.
   - On the original held-out set (commit `d026f78`), 4 of the 8 queries targeted `INEC2026-REG-S18-SS1`, which ceased to exist when the ungrounded guidelines corpus was removed in Audit 2. For the 4 queries with valid Gazette targets, the like-for-like retrieval hit rate was **1 of 4 (25.0%)** [95% Wilson CI: 4.6% - 69.9%].
   - On the revised 8-query held-out set (n=8, authored by developer test author, synthetic voter queries held out from index design) without translation assistance, Recall@3 was **25.0% (2/8)** [95% Wilson Score Interval: 7.1% - 59.1%], MRR was **0.250**.
   - With real translation step integrated (Google Cloud Translation with explicit user privacy disclosure), held-out Recall@3 reaches **75.0% (6/8)** [95% Wilson Score Interval: 40.9% - 92.9%].
   - Per-language breakdowns are suppressed because $n=2$ per language is below the statistical threshold of $n=20$.

7. **Document Ingestion Status**:
   - **Electoral Act 2026 Gazette**: Fully downloaded and parsed via `pypdf` (121 pages, SHA-256: `dee5a37b62b920c9cfaf009b7dc1dcf5ccb5cbbeff807f5487eac868ce882fd6`). Excludes Table of Contents (Pages 3-8). Main body parsed into Sections 1-156 (455 chunks); First Schedule parsed into separate paragraphs `EA2026-SCH1-P1` through `P55` (55 chunks). All 510 chunk IDs are unique.
   - **INEC Electronic Transmission Procedure**: Fully downloaded and parsed from `https://inecnigeria.org/documents/guidelines/Electronic_Transmission___Collation_Of_Result-5.pdf` (661,914 bytes, SHA-256: `95ea51c77f32229550e905ff1a0d748b0554cac178908cc91ab0ee3e17eec0c9`).
   - **18.1 MB Regulations & Guidelines 2026 PDF**: **NOT DOWNLOADED** due to severe upstream server throttling (~15 KB/s) causing network timeouts. Stale handwritten mock guidelines were completely deleted.

8. **Zero Live INEC Access**:
   - Does not touch live INEC voter registration databases, polling unit collation hardware, or IReV servers.
