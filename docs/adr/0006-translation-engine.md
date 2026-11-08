# ADR 0006: Multilingual Query Translation Engine and Nigerian Pidgin Strategy

- **Status**: Accepted (Implemented in Phase 3)
- **Date**: 2026-11-08
- **Scope**: Multilingual query translation across Hausa (`ha`), Yoruba (`yo`), Igbo (`ig`), and Nigerian Pidgin (`pcm`) to English legal search representations.

---

## 1. Context and Problem Statement

The Electoral Act 2026 is enacted and gazetted exclusively in English. To ensure equitable electoral access under Track 3 (Inclusive and Multilingual Civic Tech), Nigerian citizens querying in Hausa, Yoruba, Igbo, or Nigerian Pidgin must retrieve authoritative provisions from the official English corpus.

However, multilingual translation of statutory text carries severe risks:
1. **Semantic Drift & Hallucination**: Off-the-shelf machine translation frequently mangles legal terminology (e.g. translating Yoruba "ojo ori" as "days" instead of "age", or dropping "accreditation" / "tantance").
2. **Absence of Nigerian Pidgin in NLLB-200**: Meta's state-of-the-art open translation model `facebook/nllb-200-distilled-600M` supports 200 languages, including Hausa (`hau_Latn`), Yoruba (`yor_Latn`), and Igbo (`ibo_Latn`), but **explicitly does NOT support Nigerian Pidgin (`pcm`)** due to absence of mined parallel web data.
3. **Legal Authority Hazard (Constraint H3)**: Machine translation must never be presented to a voter as an authoritative statement of Nigerian law.

---

## 2. Decision and Architecture

We implement **`TranslationEngine`** in [`src/retrieval/translation_engine.py`](file:///C:/Users/NDIEZE/Desktop/INEC%20Hackathon/src/retrieval/translation_engine.py), integrated into [`TranslationHybridRetriever`](file:///C:/Users/NDIEZE/Desktop/INEC%20Hackathon/src/retrieval/translate_hybrid.py).

### 2.1 Multi-Tier Translation Hierarchy

```mermaid
flowchart TD
    Q[Inbound Voter Query] --> LID{Language}
    LID -->|en| ID[Identity Pass-Through]
    LID -->|pcm| PCM{Pidgin Strategy}
    PCM -->|rule_mapped (Default)| PCM_MAP[Curated Civic Lexicon Mapper]
    PCM -->|pass_through| PCM_PT[Direct English Pass-Through]
    PCM -->|abstain| PCM_ABS[Polite Abstention Notice]
    LID -->|ha / yo / ig| CACHE{In Local Cache?}
    CACHE -->|Yes| C_HIT[Cached Translation]
    CACHE -->|No| NLLB{ENABLE_NLLB_LOCAL=True?}
    NLLB -->|Yes & Weights Found| LOCAL_NLLB[Local NLLB-200 Distilled-600M]
    NLLB -->|No / Missing| OPTIN{Online Opt-In & Consent?}
    OPTIN -->|Yes| GTX[Google Translate Web Endpoint]
    OPTIN -->|No| GLOSSARY[Offline Civic Dictionary Fallback]
```

1. **Local NLLB-200**:
   - Model: `facebook/nllb-200-distilled-600M`.
   - Gated behind `ENABLE_NLLB_LOCAL=False` (default OFF for instant air-gapped reproducibility).
   - Language codes: `hau_Latn`, `yor_Latn`, `ibo_Latn` -> `eng_Latn`.
2. **Deterministic File Cache**:
   - Stored in [`data/cache/translation_cache.json`](file:///C:/Users/NDIEZE/Desktop/INEC%20Hackathon/data/cache/translation_cache.json).
3. **Opt-in Third-Party Web Endpoint**:
   - Unofficial `gtx` endpoint with mandatory consent disclosure:
     *"Do not enter personal details; the third-party service may log your text."*
   - Off by default; requires explicit runtime activation.
4. **Air-Gapped Civic Dictionary Fallback**:
   - Curated mappings for core electoral statutory concepts (e.g. *tantance*, *na'urar bvas*, *abajade*, *enyocha*, *ubochi ole*).

---

## 3. Nigerian Pidgin (`pcm`) Empirical Strategy Benchmark

Because NLLB-200 lacks Pidgin support, we conducted an empirical evaluation of three architectural handling options using [`tests/bench_pidgin_options.py`](file:///C:/Users/NDIEZE/Desktop/INEC%20Hackathon/tests/bench_pidgin_options.py) across 5 frozen civic queries in [`tests/data/lid_validation_bench.json`](file:///C:/Users/NDIEZE/Desktop/INEC%20Hackathon/tests/data/lid_validation_bench.json).

Results cached in [`data/cache/pidgin_strategy_benchmark.json`](file:///C:/Users/NDIEZE/Desktop/INEC%20Hackathon/data/cache/pidgin_strategy_benchmark.json):

| Metric | Option (a): Direct Pass-Through | Option (b): Curated Rule-Based Mapper | Option (c): Abstention |
| :--- | :---: | :---: | :---: |
| **Hit@3 Accuracy** | 80.0% (4 / 5) | **80.0% (4 / 5)** | 0.0% (0 / 5) |
| **Top-1 Accuracy** | 20.0% (1 / 5) | **60.0% (3 / 5)** | 0.0% (0 / 5) |
| **Mean Reciprocal Rank (MRR)** | 0.467 | **0.700** | 0.000 |
| **Failure Modes** | Over-voting query missed | Over-voting query missed | Fails all queries |

### Benchmark Analysis & Decision
- **Why Option (b) Wins**: Nigerian Pidgin syntax contains conversational auxiliaries (*"suppose give"*, *"which age person must reach"*) that cause token dilution in standard BM25 retrieval. Normalizing these phrases to legal civic equivalents (*"publish notice of election"*, *"minimum age 18 years"*) increases MRR by **+50.0%** (0.700 vs 0.467) and triples Top-1 accuracy (60.0% vs 20.0%).
- **Policy**: We configure `PIDGIN_HANDLING_STRATEGY="rule_mapped"` as default, while allowing `pass_through` or `abstain` via environment configuration.

---

## 4. Auditable Safeguards (Constraint H3)

1. **Non-Authoritative Tagging**:
   - All translated outputs carry `is_draft = True` and are presented as `UNREVIEWED_DEVELOPER_DRAFT`.
2. **Dual Citation Requirement**:
   - The user interface displays the verbatim English official gazette quote alongside any draft translation, ensuring the voter can always inspect the primary statutory text.
