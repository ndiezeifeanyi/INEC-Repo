# Evaluation Report: Multilingual Electoral QA and Verification

- **Evaluation Date**: 2026-11-07
- **Target Freeze Date**: 2026-11-10
- **Final Submission Date**: 2026-11-12
- **Environment**: Python 3.13.9, pytest 8.4.2

---

## 1. Retrieval Benchmark Results (Held-Out Benchmark Set)

Evaluated across 20 canonical voter questions in English (`en`), Hausa (`ha`), Yoruba (`yo`), and Igbo (`ig`) targeting exact statutory sections of the Electoral Act 2026 and INEC Regulations 2026.

```json
{
  "Path A (Cross-Lingual Vector Similarity)": {
    "Recall@1": "40.0%",
    "Recall@3": "80.0%",
    "MRR": "0.635",
    "Recall@3_by_lang": {
      "en": "80.0%",
      "ha": "80.0%",
      "yo": "100.0%",
      "ig": "60.0%"
    }
  },
  "Path B (Translate-to-English + Hybrid BM25/Dense RRF)": {
    "Recall@1": "55.0%",
    "Recall@3": "95.0%",
    "MRR": "0.750",
    "Recall@3_by_lang": {
      "en": "80.0%",
      "ha": "100.0%",
      "yo": "100.0%",
      "ig": "100.0%"
    }
  }
}
```

### Measured Findings
- **Production Architecture Selection**: Path B outperforms Path A significantly in cross-lingual retrieval (Recall@3 of **95.0%** vs 80.0%, and MRR of **0.750** vs 0.635).
- Direct cross-lingual embeddings without intermediate translation (Path A) struggle with nuanced legal concepts in Igbo (Recall@3 was only 60.0%).
- Path B achieves **100% Recall@3** across all three indigenous languages (Hausa, Yoruba, and Igbo) by leveraging certified conceptual term mapping into statutory BM25 and dense representation.
- **Architectural Decision**: Path B is accepted as the primary default retriever for production deployment.

---

## 2. Currency & Transition Verification (2026 vs Repealed 2022 Act)

- **Test Suite**: `tests/eval_currency.py`
- **Result**: **PASS (100%)**
- **Specific Validations**:
  1. No answer references the repealed Electoral Act 2022 as current law.
  2. Electronic transmission procedure is grounded in INEC Regulations 2026 Clause 38 and Electoral Act 2026 Section 50(2).
  3. Notice of election is verified at 360 days under Section 28(1) of the 2026 Act.
  4. **Section 29A Amendment Status**: Reliably classified as `PASSED_BILL_AWAITING_GAZETTE`. The engine explicitly outputs that Section 29A has passed the National Assembly (SB.412/HB.890) but awaits formal presidential assent and official gazetting, preventing voter confusion.

---

## 3. Red-Team, Safety & Partisan Refusal Evaluation

- **Test Suite**: `tests/test_red_team.py`
- **Result**: **PASS (100% Refusal Rate)**
- **Breakdown**:
  - **Candidate Endorsement / Comparison Bait**: 100% refused in EN, HA, YO, and IG.
  - **Election Outcome Predictions**: 100% refused with directive to await official INEC returns.
  - **Tribunal Litigation Advice**: 100% refused with recommendation to consult a qualified legal practitioner.
  - **Prompt Injections (System Override / Forced Victory)**: 100% refused.
  - **Out-of-Scope Non-Electoral Queries**: 100% abstained, redirecting to `https://inecnigeria.org`.
  - **Citation Leakage**: 0% citation leakage on refused prompts.

---

## 4. Check Mode (Link & Message Verification)

- **Test Suite**: `tests/test_check_mode.py`
- **Result**: **PASS (100%)**
- **Test Matrix**:
  - `https://inecnigeria.org/elections/guidelines` -> `Matches an official source`
  - `https://cvr.inecnigeria.org` -> `Matches an official source` (**0% False Positive despite third-party CNAME delegation**)
  - `https://irev.inecnigeria.org` -> `Matches an official source`
  - `http://linksnapro.com/cvrreg` -> `Does not match any official source I can check` (Flagged as known counterfeit)
  - `https://pvc-inecnigeria-org.blogspot.com` -> `Does not match any official source I can check` (Flagged as known counterfeit)
  - `https://1nec-nigeria.org/portal` -> `Does not match any official source I can check` (Flagged as typosquat)
  - Official published election timetable message -> `Matches an official source`
  - Fabricated "cancelled elections" viral rumor -> `Does not match any official source I can check`
  - Unverifiable generic comment -> `Can't tell`
  - **Mandatory Disclaimer**: Present on 100% of responses.

---

## 5. Licences, Limitations, and Unverified Items

1. **Licensing Compliance**:
   - Meta MMS-TTS: `CC-BY-NC-4.0` (Attribution displayed; non-commercial research use only).
   - N-ATLaS LLM Candidate: Gated research license capped at 1,000 active users/month.
   - Core Project Code: `MIT License`.
2. **Linguistic Scope & Native Reviewers**:
   - Primary civic glossaries seeded from Masakhane & BBC News civic corpora.
   - Reviewer signatures recorded in `data/glossaries/*.json`.
   - Pidgin support remains **strictly disabled** until formal multi-speaker evaluation and $\kappa \ge 0.85$ inter-annotator agreement is achieved.
3. **Payload Budget**:
   - Web application payload (HTML + CSS + JS) is **under 20 KB** (well within the 30 KB budget), validated for 2G/EDGE networks.
