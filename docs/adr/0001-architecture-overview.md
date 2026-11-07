# ADR 0001: Architecture Overview and System Boundaries

- **Status**: Accepted
- **Date**: 2026-11-07
- **Author**: Senior AI & Software Engineer
- **Context**: #AI4Elections Hackathon (Track 3: Inclusive and Multilingual Civic Tech)

## Decision

We adopt a decoupled, evidence-first, privacy-preserving architecture consisting of:
1. **Statutory Ingestion Engine**: Deterministic parsing of official legal documents (Electoral Act 2026, INEC Guidelines 2026) chunked strictly by legal demarcation (Part, Section, Subsection), hashed with SHA-256.
2. **Dual-Path Retrieval Evaluation**: Benchmarking Path A (Direct Cross-lingual Dense Retrieval via AfriE5/BGE-M3) against Path B (Query Translation + BM25/Dense Hybrid Retrieval) to pick the superior empirical performer.
3. **Grounded Generation & Glossary Layer**: Mandatory citation of Document, Section, Version, and Date. Strict refusal of political questions, candidates, predictions, or legal advice. Automatic enforcement of bilingual civic glossaries (Hausa, Yoruba, Igbo).
4. **Privacy-Preserving Check Engine**: Three-state output ("Matches an official source", "Does not match any official source I can check", "Can't tell"). URL verification through domain allowlisting (accounting for CNAME delegation on cvr.inecnigeria.org), typosquatting/homoglyph detection, and privacy-preserving Google Safe Browsing Update API v4 (4-byte local SHA-256 prefix hash database; zero transmission of full URLs).
5. **Accessible Web & API Delivery**: Fast, ultra-low bandwidth semantic HTML/CSS web client (<30 KB initial payload) backed by a FastAPI REST API ready for bot and USSD consumption.

## Consequences

- Zero user PII is ever collected or persisted.
- No live INEC infrastructure (including IReV) is scraped or contacted.
- Model hallucinations are prevented by rejecting ungrounded queries and returning standard abstention responses pointing to inecnigeria.org.

