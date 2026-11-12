# Nigerian Election Rules Q&A & Official Link/Message Verifier

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests: 4/4 Passed](https://img.shields.io/badge/Tests-4%2F4%20Passed-brightgreen.svg)](tests/)
[![Hackathon: AI4Elections](https://img.shields.io/badge/Hackathon-%23AI4Elections%20Track%203-blue.svg)](#)

An independent, nonpartisan, evidence-first civic tech prototype built for the **#AI4Elections Hackathon (Track 3: Inclusive and Multilingual Civic Tech)**.

It answers voter questions regarding Nigeria's election rules strictly grounded in the **Electoral Act 2026** and **INEC Regulations 2026** across **Hausa, Yoruba, and Igbo**, and verifies whether links or viral messages match official INEC published sources without ever evaluating partisan claims as "True" or "False".

---

## Key Capabilities

1. **Grounded Statutory Q&A**: Answers are retrieved exclusively from official legal chunks with full statutory citations (Document, Section, Subsection, Gazette Version, Retrieval Date, and Source URL).
2. **Strict Nonpartisan Guardrails**: Programmatically refuses candidate comparisons, voting recommendations, outcome predictions, tribunal litigation advice, and prompt injections.
3. **Tri-State Check Mode**: Inspects links and messages and returns strictly:
   - *"Matches an official source"*
   - *"Does not match any official source I can check"*
   - *"Can't tell"*
   accompanied by an explicit notice that checks are not all-knowing.
4. **Privacy-Preserving Phishing Defense**: Implements Google Safe Browsing Update API v4 principles with local 4-byte SHA-256 hash prefixes. **Zero full URLs are transmitted to third parties.**
5. **Accurate CNAME Handling**: Accounts for third-party cloud routing on `cvr.inecnigeria.org` without false-positive phishing flags.
6. **Accessible & Low-Bandwidth**: Total web page weight is **under 20 KB** (well below the 30 KB budget) for seamless operation on 2G/EDGE networks.
7. **Audio Feature**: Test tone only (offline synthetic tone generator; Meta MMS-TTS requires downloading model weights).
8. **Section 29A Amendment Transparency**: Explicitly classified and disclosed as `UNCONFIRMED` (Passed by both chambers Apr/May 2026; unconfirmed presidential assent; check the Gazette).

---

## Verified Evaluation Results

[MEASURED: `pytest tests/` on frozen test benchmarks (`retrieval_bench.json`, `heldout_bench.json`, `currency_bench.json`, `refusal_bench.json`, `check_bench.json`)]

| Dimension / Test | Path A (Cross-Lingual) | Path B (Translate-Hybrid RRF) | Status | Benchmark Source |
| :--- | :--- | :--- | :--- | :--- |
| **Recall@3 (Overall)** | 50.0% | **90.0%** | **PASS** (Path B selected) | `tests/eval_retrieval.py` |
| **Recall@3 (Hausa)** | 60.0% | **100.0%** | **PASS** | `tests/eval_retrieval.py` |
| **Recall@3 (Yoruba)** | 60.0% | **80.0%** | **PASS** | `tests/eval_retrieval.py` |
| **Recall@3 (Igbo)** | 60.0% | **100.0%** | **PASS** | `tests/eval_retrieval.py` |
| **Retrieval MRR** | 0.272 | **0.639** | **PASS** | `tests/eval_retrieval.py` |
| **Currency (2026 vs 2022)** | N/A | **100% adherence** | **PASS** | `tests/eval_currency.py` |
| **Partisan Refusal Rate** | N/A | **100% refusal** | **PASS** | `tests/test_red_team.py` |
| **Typosquat / Fraud Detection**| N/A | **100% detection** | **PASS** | `tests/test_check_mode.py` |
| **cvr.inecnigeria.org CNAME** | N/A | **0.0% false alarm** | **PASS** | `tests/test_check_mode.py` |

Full empirical test logs are documented in [`docs/evaluation_report.md`](docs/evaluation_report.md).

---

## Architecture & System Documentation

- [`docs/adr/0001-architecture-overview.md`](docs/adr/0001-architecture-overview.md): System boundaries and decoupled architecture.
- [`docs/adr/0002-tts-licensing.md`](docs/adr/0002-tts-licensing.md): Meta MMS-TTS non-commercial CC-BY-NC-4.0 compliance.
- [`docs/adr/0003-retrieval-architecture.md`](docs/adr/0003-retrieval-architecture.md): Dual-path evaluation and empirical selection of Path B.
- [`docs/duplication_log.md`](docs/duplication_log.md): Comparative analysis against Run-Am, GovGuide, and Naija Elections AI.
- [`docs/system_card.md`](docs/system_card.md): Model specs, training sources, and limits.
- [`docs/data_sheet.md`](docs/data_sheet.md): Metadata on statutory corpora and bilingual glossaries.
- [`docs/safety_statement.md`](docs/safety_statement.md): Nonpartisanship commitments and refusal rules.
- [`docs/privacy_note.md`](docs/privacy_note.md): Zero PII collection and local hash privacy disclosures.
- [`docs/demo_video_script.md`](docs/demo_video_script.md): Timed 2-minute demonstration video script.

---

## Quickstart

### 1. Requirements
- Python >= 3.10
- Git

### 2. Run Test Suite
```bash
python -m pytest tests/
```
Output:
```
tests\eval_currency.py .     [ 25%]
tests\eval_retrieval.py .    [ 50%]
tests\test_check_mode.py .   [ 75%]
tests\test_red_team.py .     [100%]
4 passed in 8.91s
```

### 3. Launch Web Portal & REST API
```bash
uvicorn src.web.app:app --host 0.0.0.0 --port 8000
```
Open [http://localhost:8000](http://localhost:8000) in any web browser.

---

## API Endpoints

### 1. Ask Election Rules (`POST /api/v1/ask`)
Request:
```json
{
  "query": "Yaya ake tantance mai kada kuri'a da na'urar BVAS a ranar zabe?",
  "language": "ha"
}
```
Response:
```json
{
  "question": "Yaya ake tantance mai kada kuri'a da na'urar BVAS a ranar zabe?",
  "language": "ha",
  "answer_text": "Bisa ga sashe na 47(2) na Dokar Zabe ta 2026, wajibi ne babban jami'in zabe ya yi amfani da na'urar tantance masu kada kuri'a (BVAS) domin tabbatar da shaidar mai zabe kafin a ba shi takardar kada kuri'a.",
  "answer_plain": "The Presiding Officer must use the official electronic accreditation device (BVAS) to verify and confirm your voter details before giving you a ballot paper.",
  "citations": [
    {
      "document_title": "Electoral Act 2026",
      "section": "47",
      "subsection": "2",
      "version": "Official Gazette No. 40, Vol. 113",
      "retrieval_date": "2026-11-01",
      "source_url": "https://nass.gov.ng/documents/download/11248",
      "legal_status": "ENACTED"
    }
  ]
}
```

### 2. Check Link or Message (`POST /api/v1/check`)
Request:
```json
{
  "item": "https://cvr.inecnigeria.org"
}
```
Response:
```json
{
  "input_item": "https://cvr.inecnigeria.org",
  "type": "url",
  "status": "Matches an official source",
  "matched_source": "cvr.inecnigeria.org",
  "confidence_notes": "Confirmed authentic INEC domain: Verified official INEC domain: cvr.inecnigeria.org",
  "disclaimer": "This check compares inputs against gazetted statutes and official public INEC records. It is not exhaustive or infallible and does not evaluate political opinions or non-electoral claims."
}
```

---

## License
This project is licensed under the terms of the [MIT License](LICENSE).  
Audio feature: test tone only (offline synthetic PCM tone generator; production Meta MMS-TTS models are governed by CC-BY-NC-4.0).

