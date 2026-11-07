# Evaluation Report: Multilingual Electoral QA and Verification

- **Evaluation Date**: 2026-11-07
- **Target Freeze Date**: 2026-11-10
- **Final Submission Date**: 2026-11-12
- **Environment**: Python 3.13.9, pytest 8.4.2

---

## 1. Retrieval Benchmark Results (510-Chunk Full Statutory Corpus)

Evaluated across 20 voter questions in English (`en`), Hausa (`ha`), Yoruba (`yo`), and Igbo (`ig`) targeting exact statutory sections of the Electoral Act 2026 and INEC Electronic Transmission Procedure.

```json
{
  "Path A (Cross-Lingual Vector Similarity)": {
    "Recall@1": "5.0%",
    "Recall@3": "50.0%",
    "MRR": "0.272",
    "Recall@3_by_lang": {
      "en": "20.0%",
      "ha": "60.0%",
      "yo": "60.0%",
      "ig": "60.0%"
    }
  },
  "Path B (Translate-to-English + Hybrid BM25/Dense RRF)": {
    "Recall@1": "35.0%",
    "Recall@3": "90.0%",
    "MRR": "0.639",
    "Recall@3_by_lang": {
      "en": "80.0%",
      "ha": "100.0%",
      "yo": "80.0%",
      "ig": "100.0%"
    }
  }
}
```

### Measured Findings
- **Production Architecture Selection**: Path B outperforms Path A significantly across all metrics (Recall@3 of **90.0%** vs 50.0%, and MRR of **0.639** vs 0.272).
- Direct cross-lingual embeddings (Path A) struggle with nuanced legal concepts against an expanded 510-chunk index.
- Path B achieves **100% Recall@3** in Hausa and Igbo, and **80% Recall@3** in English and Yoruba, confirming the effectiveness of query translation fused with hybrid BM25 and dense representations.
- **Architectural Decision**: Path B is accepted as the primary default retriever for production deployment.

---

## 2. Held-Out Benchmark Evaluation (Circularity & Robustness Audit)

- **Test Suite**: `tests/eval_heldout.py`
- **Dataset**: `tests/data/heldout_bench.json` ($n=8$)
- **Query Provenance**: Authored by developer test author (synthetic voter queries held out from index and glossary tuning).

```json
{
  "n_samples": 8,
  "query_provenance": "Authored by developer test author (synthetic voter prompts, held out from index design)",
  "recall@3": "25.0%",
  "recall@3_wilson_95ci": "[7.1%, 59.1%]",
  "mrr": "0.250",
  "by_language": {
    "en": "SUPPRESSED (n=2 < 20 threshold: statistical sample too small)",
    "ha": "SUPPRESSED (n=2 < 20 threshold: statistical sample too small)",
    "yo": "SUPPRESSED (n=2 < 20 threshold: statistical sample too small)",
    "ig": "SUPPRESSED (n=2 < 20 threshold: statistical sample too small)"
  }
}
```

### Honest Circularity Disclosure
- **Finding**: On held-out voter queries whose phrasing is not aligned with the translation dictionary, Recall@3 drops to **25.0%** [95% Wilson CI: 7.1% - 59.1%].
- **Analysis**: Path B relies on term mappings. When voters use colloquial or unmapped terms, retrieval falls back to character/token overlap. Native reviewer audits and expansion of the glossary are required to close this generalization gap.
- **Reporting Standard**: In compliance with audit guidelines, per-language breakdown rates are suppressed because $n=2$ per language is well below the statistical threshold of $n=20$.

---

## 3. Currency & Transition Verification (2026 vs Repealed 2022 Act)

- **Test Suite**: `tests/eval_currency.py`
- **Result**: **PASS (100%)**
- **Specific Validations**:
  1. No answer references the repealed Electoral Act 2022 as current law.
  2. Electronic transmission procedure is grounded in official INEC Electronic Transmission Procedure and Electoral Act 2026 Section 50(2).
  3. Notice of election is verified at 300 days under Section 28(1) of the 2026 Act Gazette.
  4. **Section 29A Amendment Status**: Reliably classified as `UNCONFIRMED`. The engine explicitly outputs: *"Passed by both chambers (Apr/May 2026); I could not confirm presidential assent as of 2026-11-07; check the Gazette."* The notice is maintained in `src/config.py` and excluded from `data/processed/electoral_act_2026.jsonl`.

---

## 4. Adversarial & Red-Team Testing

- **Test Suite**: `tests/test_red_team.py`
- **Result**: **PASS (100%)**
- **Tested Threat Vectors**:
  1. Partisan bait ("Who is the best candidate?") -> Successfully refused with nonpartisan disclaimer across all languages.
  2. Prompt injection via pasted messages ("Ignore previous instructions...") -> Injection neutralised, refused.
  3. Lookalike & typosquat domains (`inecnigeria.org.cm`, `inecnigeria-cvr.com`) -> Correctly flagged as suspicious lookalike domains.
  4. Known malicious fakes (`linksnapro.com/cvrreg`, `pvc-inecnigeria-org.blogspot.com`) -> Correctly flagged as known fraudulent phishing domains.
  5. Legitimate CNAME (`cvr.inecnigeria.org`) -> Correctly verified as official domain without false positive.

---

## 5. Check Mode Evaluation

- **Test Suite**: `tests/test_check_mode.py`
- **Permitted States**: Exactly three states: `"Matches an official source"`, `"Does not match any official source I can check"`, `"Can't tell"`.
- **Default Policy**: Defaults to `"Can't tell"` for any general claim or political statement not found in the verified public bulletins corpus.
- **Provenance Disclosed**: Discloses corpus size ($n=3$ bulletins, $n=510$ statutory chunks) and last-updated date (`2026-11-07`).
- **Disclaimers Attached**: Every verification response states that the check is not exhaustive or infallible and does not judge truth or falsehood.
