# System Card: INEC Civic Q&A and Verification Engine

## 1. System Overview
- **System Name**: Multilingual Civic Tech Electoral Verification System
- **Repository**: Public (MIT License)
- **Primary Task**:
  1. Answer Nigerian voter questions regarding election rules strictly grounded in the Electoral Act 2026 and INEC Regulations 2026 in Hausa, Yoruba, and Igbo.
  2. Verify whether a link or pasted public message matches official published INEC sources.
- **Intended Users**: Nigerian voters, civic advocates, journalists, and grassroots election observers.
- **Prohibited Uses**: Judging political claims, comparing political parties or candidates, predicting election outcomes, giving election petition legal advice, automated high-frequency polling.

## 2. Models Used
- **Embeddings**:
  - `BAAI/bge-m3` (Apache 2.0)
  - `castorini/afrie5-large-instruct` (Apache 2.0 / research)
- **Generation & Translation**:
  - Frontier Multilingual API (e.g. Gemini / Claude / GPT) with Zero Data Retention
  - `facebook/nllb-200-distilled-600M` (CC-BY-NC 4.0 / MIT equivalents)
  - Candidate LLM: `NCAIR1/N-ATLaS` (Open-Source Research License v1.0, 1,000 active users/month cap)
- **Audio / TTS**:
  - Meta MMS-TTS (`facebook/mms-tts-hau`, `yor`, `ibo`) under `CC-BY-NC-4.0`.

## 3. Performance Metrics Target
- Cross-Lingual Recall@5: $\ge 0.85$
- Retrieval MRR: $\ge 0.75$
- Statutory Citation Precision: $100\%$
- Grounded Faithfulness: $\ge 98\%$
- Partisan Refusal Accuracy: $100\%$
- CVR CNAME False Positive Rate: $0.0\%$

## 4. Known Limitations & Failure Modes
- The system cannot determine whether an unpublished or local verbal statement was actually uttered by an electoral officer unless published in an official INEC bulletin.
- Dialectal variations: Standard Hausa (Kano), Standard Yoruba (Oyo/Lagos), and Standard Central Igbo are used. Regional idioms may require fallback to English legal terms.
- Pidgin support is explicitly disabled until validation and certified glossary sign-off is completed.
