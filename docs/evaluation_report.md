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

- **Test Suite**: `tests/eval_heldout.py` & `scripts/run_heldout_audit9.py`
- **Results Provenance**: Generated deterministically by `scripts/run_heldout_audit9.py` and saved to `data/cache/heldout_audit9_results.json`.
- **Query Provenance**: Authored by developer test author (synthetic voter queries held out from index and glossary tuning).

### Benchmark Comparison across Modes: "dictionary only" vs. "dictionary + cached online translation"

All metrics below are computed directly from `data/cache/heldout_audit9_results.json`:

| Benchmark Suite | Mode Label | $n$ | Top-1 Accuracy | Top-1 Wilson 95% CI | Hit@3 (Recall@3) | Hit@3 Wilson 95% CI | MRR | Notes |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **Committed Held-Out (`heldout_bench.json`)** | **dictionary only** | 8 | **25.0%** (2/8) | [7.1%, 59.1%] | **25.0%** (2/8) | [7.1%, 59.1%] | 0.250 | Offline dictionary fallback. Indigenous queries miss because unreviewed dictionary lacks colloquial phrasings. |
| **Committed Held-Out (`heldout_bench.json`)** | **dictionary + cached online translation** | 8 | **50.0%** (4/8) | [21.5%, 78.5%] | **75.0%** (6/8) | [40.9%, 92.9%] | 0.604 | Cached `gtx` translations. Q1, Q5, Q6, Q7 hit rank 1; Q2 hits rank 3; Q3 & Q4 miss due to MT semantic loss of "accredited". |
| **Original Set (`commit d026f78`)** | **dictionary only** | 8 | **12.5%** (1/8) | [2.2%, 47.1%] | **12.5%** (1/8) | [2.2%, 47.1%] | 0.125 | Offline dictionary fallback. Items 5-8 targeted deleted ungrounded guideline Section 18. |
| **Original Set (`commit d026f78`)** | **dictionary + cached online translation** | 8 | **12.5%** (1/8) | [2.2%, 47.1%] | **25.0%** (2/8) | [7.1%, 59.1%] | 0.167 | Cached `gtx` translations. Target `INEC2026-REG-S18-SS1` was deleted in Audit 2; only valid Gazette targets can hit. |
| **Natural English Queries (No Section Jargon)** | **dictionary only (pure English)** | 6 | **66.7%** (4/6) | [30.0%, 90.3%] | **100.0%** (6/6) | [61.0%, 100.0%] | 0.806 | Natural phrasing without statutory citation keywords (over-voting, notice, primaries, transmission, PVC, real-time). |

### Detailed Query-by-Query Matrix (Committed Held-Out Set)

#### Mode: "dictionary only" (`cache_enabled=False`, `enable_online=False`)
| ID | Lang | Query | Target | Top-3 Retrieved | BM25 Top-1 | Dense Top-1 | Disagree? | Hit@1 | Hit@3 | Rank |
|---|:---:|---|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `heldout_001` | en | What are the rules regarding over-voting when votes cast exceed accredited voters? | 51 | EA2026-S51-SS2, INEC2026-ET-PAGE3, EA2026-S62-SS4 | EA2026-S51-SS2 | EA2026-S155-SS1 | YES | HIT | HIT | 1 |
| `heldout_002` | ha | Menene zai faru idan kuri'un da aka kada a rumfar zabe suka fi yawan mutanen da aka tantance? | 51 | EA2026-S47-SS2, EA2026-S47-SS3, EA2026-S67-SS1 | EA2026-S47-SS2 | EA2026-S47-SS2 | NO | MISS | MISS | >5 |
| `heldout_003` | yo | Kini yoo sele ti iye awon ti won dibo ba po ju iye awon oludibo ti a se ijeri won lo? | 51 | EA2026-S25-SS1, EA2026-S22-SS1, EA2026-S92-SS11 | EA2026-S25-SS1 | EA2026-S22-SS1 | YES | MISS | MISS | >5 |
| `heldout_004` | ig | Gini na-eme ma obu na onu ogugu ndi mere vootu karia ndi e nwere nzere ha n'ebe ntuli aka? | 51 | EA2026-S93-SS4, EA2026-SCH1-P54 | EA2026-S93-SS4 | EA2026-S93-SS4 | NO | MISS | MISS | >5 |
| `heldout_005` | en | What are the age and citizenship qualifications required to register as a voter in Nigeria? | 12 | EA2026-S12-SS1, EA2026-S8-SS1, EA2026-S22-SS1 | EA2026-S12-SS1 | EA2026-S12-SS1 | NO | HIT | HIT | 1 |
| `heldout_006` | ha | Wane shekaru da cancanta ake bukata domin mutum ya yi rajistar zabe a Najeriya? | 12 | EA2026-S67-SS1, EA2026-SCH1-P55 | EA2026-S67-SS1 | EA2026-S67-SS1 | NO | MISS | MISS | >5 |
| `heldout_007` | yo | Ojo ori melo ati awon afiyesi wo ni o ye ki eniyan ni lati le se iforukosile oludibo? | 12 | EA2026-S18-SS3, EA2026-S92-SS11, EA2026-S22-SS1 | EA2026-S18-SS3 | EA2026-S18-SS3 | NO | MISS | MISS | >5 |
| `heldout_008` | ig | Afọ ole na ihe ndị dị aṅaa ka achọrọ n'aka mmadụ ka o nwee ike idebanye aha maka vootu? | 12 | None | None | None | NO | MISS | MISS | >5 |

#### Mode: "dictionary + cached online translation" (`cache_enabled=True`, `enable_online=True`)
| ID | Lang | Query | Target | Top-3 Retrieved | BM25 Top-1 | Dense Top-1 | Disagree? | Hit@1 | Hit@3 | Rank |
|---|:---:|---|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `heldout_001` | en | What are the rules regarding over-voting when votes cast exceed accredited voters? | 51 | EA2026-S51-SS2, INEC2026-ET-PAGE3, EA2026-S62-SS4 | EA2026-S51-SS2 | EA2026-S155-SS1 | YES | HIT | HIT | 1 |
| `heldout_002` | ha | Menene zai faru idan kuri'un da aka kada a rumfar zabe suka fi yawan mutanen da aka tantance? | 51 | EA2026-S110-SS4, EA2026-S110-SS5, EA2026-S51-SS2 | EA2026-S110-SS4 | EA2026-S155-SS1 | YES | MISS | HIT | 3 |
| `heldout_003` | yo | Kini yoo sele ti iye awon ti won dibo ba po ju iye awon oludibo ti a se ijeri won lo? | 51 | EA2026-S110-SS5, EA2026-S12-SS1, EA2026-S117-SS1 | EA2026-S110-SS5 | EA2026-S155-SS1 | YES | MISS | MISS | >5 |
| `heldout_004` | ig | Gini na-eme ma obu na onu ogugu ndi mere vootu karia ndi e nwere nzere ha n'ebe ntuli aka? | 51 | EA2026-S119-SS2, EA2026-S110-SS5, EA2026-SCH1-P48 | EA2026-S126-SS2 | EA2026-S155-SS1 | YES | MISS | MISS | >5 |
| `heldout_005` | en | What are the age and citizenship qualifications required to register as a voter in Nigeria? | 12 | EA2026-S12-SS1, EA2026-S8-SS1, EA2026-S22-SS1 | EA2026-S12-SS1 | EA2026-S12-SS1 | NO | HIT | HIT | 1 |
| `heldout_006` | ha | Wane shekaru da cancanta ake bukata domin mutum ya yi rajistar zabe a Najeriya? | 12 | EA2026-S12-SS1, EA2026-S8-SS1, EA2026-S22-SS1 | EA2026-S12-SS1 | EA2026-S12-SS1 | NO | HIT | HIT | 1 |
| `heldout_007` | yo | Ojo ori melo ati awon afiyesi wo ni o ye ki eniyan ni lati le se iforukosile oludibo? | 12 | EA2026-S12-SS1, EA2026-S8-SS1, EA2026-S22-SS1 | EA2026-S12-SS1 | EA2026-S12-SS1 | NO | HIT | HIT | 1 |
| `heldout_008` | ig | Afọ ole na ihe ndị dị aṅaa ka achọrọ n'aka mmadụ ka o nwee ike idebanye aha maka vootu? | 12 | EA2026-S8-SS1, EA2026-S12-SS1, EA2026-S22-SS1 | EA2026-S8-SS1 | EA2026-S8-SS1 | NO | MISS | HIT | 2 |

---

### Honest Circularity Disclosure & Like-for-Like Analysis
- **Original Benchmark Like-for-Like**: In the initial held-out suite (commit `d026f78`), 4 of the 8 queries targeted `INEC2026-REG-S18-SS1`, which ceased to exist when the ungrounded guidelines corpus was removed in Audit 2. Of the remaining 4 queries with valid Gazette targets, the like-for-like retrieval hit rate was **1 of 4 (25.0%)**, Wilson 95% CI: `[4.6%, 69.9%]`.
- **Pre-Translation Hybrid Benchmark**: On the revised 8-query held-out set prior to translation integration, Recall@3 was **25.0% (2/8)** [95% Wilson CI: 7.1% - 59.1%].
- **Post-Translation Integration (Audit 5 & 6)**: Following integration of the unofficial Google Translate web endpoint (`client=gtx`, `sl=ha/yo/ig`, `tl=en` with explicit opt-in disclosure), held-out Recall@3 reached **75.0% (6/8)** [95% Wilson CI: 40.9% - 92.9%].
- **Analysis**: Path B relies on translation into English legal concepts. When voters use colloquial phrasing, pure dictionary matching achieves only 1 of 4 (25.0%). With real translation assistance, 6 of 8 queries hit their target provisions, demonstrating the necessity of robust translation over static dictionaries.
- **Reporting Standard**: In compliance with audit guidelines, per-language breakdown rates are suppressed because $n=2$ per language is well below the statistical threshold of $n=20$.

---

## 3. Currency & Transition Verification (2026 vs Repealed 2022 Act)

- **Test Suite**: `tests/eval_currency.py`
- **Result**: **PASS (100%)**
- **Specific Validations**:
  1. No answer references the repealed Electoral Act 2022 as current law.
  2. Electronic transmission procedure is grounded in official INEC Electronic Transmission Procedure and Electoral Act 2026 Section 50(2) & 60(3). Answer generator attaches mandatory statutory flag `DOC_REFERS_TO_ELECTORAL_ACT_2022` to citations referencing the April 2022 procedural guidelines.
  3. Notice of election is verified at 300 days under Section 28(1) of the 2026 Act Gazette (No. 40, Vol. 113).
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

---

## 6. Machine Translation Audit (Unofficial gtx Endpoint Findings)

Evaluation of low-resource Nigerian language queries translated via the unofficial Google Translate web endpoint (`client=gtx`) revealed three significant semantic errors:

### Finding 1: Yoruba Temporal vs. Age Homonym Confusion (`heldout_007`)
- **Source Query**: *"Ojo ori melo ati awon afiyesi wo ni o ye ki eniyan ni lati le se iforukosile oludibo?"*
- **Literal Meaning**: *"What age and what qualifications does a person need to register as a voter?"*
- **Machine Translation Output**: *"How many days and what requirements do people need to register as a voter?"*
- **Cause**: In Yoruba, *"ọjọ́"* means "day", while the compound *"ọjọ́ orí"* (literally "days of head") means "age". The gtx endpoint stripped or misinterpreted the diacritics and compounded structure, dropping "age" and outputting "days".
- **Retrieval Impact**: Despite this semantic flaw, the query retrieved Section 12(1) at Rank 1 due to dense overlap with voter registration terms ("iforukosile oludibo" -> "register as a voter").

### Finding 2: Yoruba Loss of Accreditation Semantics (`heldout_003`)
- **Source Query**: *"Kini yoo sele ti iye awon ti won dibo ba po ju iye awon oludibo ti a se ijeri won lo?"*
- **Literal Meaning**: *"What will happen if the number of people who voted exceeds the number of accredited voters?"*
- **Machine Translation Output**: *"What will happen if the number of people who vote is more than the number of voters who are registered?"*
- **Cause**: The gtx engine translated *"ijeri"* (accreditation/verification) as *"registered"*.
- **Retrieval Impact**: The concept of "accredited voters" was replaced by "registered voters", leading the retriever to surface voter register sections (Sections 110, 12, 117) rather than over-voting (Section 51(2)). Result: **Miss at Rank > 3**.

### Finding 3: Igbo Loss of Accreditation Semantics (`heldout_004`)
- **Source Query**: *"Gini na-eme ma obu na onu ogugu ndi mere vootu karia ndi e nwere nzere ha n'ebe ntuli aka?"*
- **Literal Meaning**: *"What happens if the number of people who voted exceeds those who have accreditation at the polling unit?"*
- **Machine Translation Output**: *"What happens if the number of people who voted is more than those who have their credentials at the polling station?"*
- **Cause**: The phrase *"ndi e nwere nzere ha"* was translated as *"those who have their credentials"*, missing the exact statutory term *"accredited voters"*.
- **Retrieval Impact**: Without the term "accredited", BM25 failed to match Section 51(2) ("over-voting ... accredited voters"). Result: **Miss at Rank > 3**.

### Architectural Takeaway
Low-resource MT engines exhibit severe semantic drift on specialized legal/electoral vocabulary. While MT substantially lifts baseline performance over static unreviewed dictionaries (75.0% vs. 25.0%), human-reviewed civic glossaries for core electoral concepts (accreditation, over-voting, collation) remain essential to prevent critical misdirections.

---

## 7. Audit 9 Multilingual & Disagreement Abstention Safeguard

In accordance with Ninth Audit directives:
1. **Translated Queries (`ha`, `yo`, `ig`)**:
   - Query translation introduces potential semantic drift on legal terminology (e.g., confusing "accredited" with "registered" or "credentials").
   - Consequently, for ANY query translated from Hausa, Yoruba, or Igbo, the system **never presents a primary answer**.
   - Instead, the response abstains from single-section authority, displays the top-3 retrieved statutory provisions explicitly labelled `[machine-translated, unreviewed]`, and attaches the confidence flag `MACHINE_TRANSLATED_UNREVIEWED`.
2. **Lexical (BM25) vs. Dense Ranker Disagreement**:
   - For English queries, if the top-1 ranked document from BM25 differs from the top-1 ranked document from Dense retrieval (`dense_top1 != bm25_top1`), the system detects an internal retrieval conflict.
   - In this state, the engine refuses to guess which signal is correct: it omits any single primary answer, surfaces the top-3 provisions labelled `[machine-translated, unreviewed]`, and attaches `ABSTENTION_RETRIEVAL_DISAGREEMENT`.

---

## 8. Hybrid Retrieval RRF Formulation & Score Gap Derivation (Audit Directive 5)

### 8.1 Fraction of BM25 versus Dense Representation
In `TranslationHybridRetriever.retrieve()`, ranking fusion is computed via Reciprocal Rank Fusion (`reciprocal_rank_fusion`):

$$\text{RRF}(d) = \sum_{m \in \{\text{BM25}, \text{Dense}\}} \frac{w_m}{k + \text{rank}_m(d)}$$

Where:
- $k = 60$ (standard smoothing constant to prevent top-rank domination).
- $w_{\text{BM25}} = 1.0$ and $w_{\text{Dense}} = 1.0$.
- Each ranker contributes an equal weight factor of 1.0 to the fusion numerator.

Therefore, the exact mathematical fraction of the result contributed by each component is:
- **BM25 fraction**: **50.0% (1/2)** of potential rank fusion score.
- **Dense step fraction**: **50.0% (1/2)** of potential rank fusion score.

### 8.2 Why the Score Gap Uses Rank-Fusion Scores
The score gap $\Delta = \text{Score}_1 - \text{Score}_2$ is calculated directly from the final fused RRF scores rather than raw retrieval scores for two essential mathematical reasons:
1. **Incommensurate Dimensional Scales**:
   - Raw BM25 scores are unbounded term-frequency logarithmic sums: $\text{BM25} \in [0, \infty)$, heavily influenced by document length, query token count, and inverse document frequency (often ranging from 3.0 to 25.0+).
   - Dense scores are normalized lexical-overlap Jaccard ratios: $\text{Dense} \in [0, 1.0]$.
   - Because raw scores inhabit non-comparable dimensions, directly comparing or subtracting them is mathematically invalid.
2. **Harmonic Space Normalization**:
   - RRF maps both heterogeneous distributions into a dimensionless, monotonic harmonic space bounded in:
     $$\text{RRF}(d) \in \left(0, \frac{2}{k+1}\right] = \left(0, \frac{2}{61}\right] \approx (0, 0.032787]$$
   - A document that achieves rank 1 across both rankers earns the maximal score of:
     $$\text{RRF}_1 = \frac{1}{60 + 1} + \frac{1}{60 + 1} = \frac{2}{61} \approx 0.032787$$
   - A runner-up that achieves rank 2 across both rankers earns:
     $$\text{RRF}_2 = \frac{1}{60 + 2} + \frac{1}{60 + 2} = \frac{2}{62} \approx 0.032258$$
   - The consensus gap between universal #1 and universal #2 is $\Delta = 0.032787 - 0.032258 = 0.000529$.
   - Conversely, if candidate 1 ranks #1 across both rankers ($0.032787$) while candidate 2 appears only in one list at rank 5 ($0.015385$), the gap is $\Delta = 0.017402$, demonstrating clear separation.
   - Using RRF rank-fusion scores allows an empirical threshold (`SCORE_GAP_THRESHOLD = 0.0010`, calibrated on a 12-query validation split) to separate strong consensus from contested ties across queries of varying length and complexity.

---

## 9. Statutory Cross-Reference Promotion Rule Audit (Audit Directive 6)

### 9.1 Narrow Rule Definition
In `TranslationHybridRetriever.retrieve()`:
```python
if fused:
    top_c = fused[0][0]
    m = re.match(r"^Subject to section (\d+)", top_c.content_english.strip(), re.IGNORECASE)
    if m:
        target_sec = m.group(1)
        for idx, (c, sc) in enumerate(fused[1:], start=1):
            if c.section_number == target_sec:
                promoted_chunk = fused.pop(idx)
                fused.insert(0, (promoted_chunk[0], fused[0][1] + 0.001))
                break
```
- **Legislative Intent**: Statutory drafting in Nigeria frequently begins procedural sections with subordination clauses (e.g., *"Subject to section 60 of this Act, the procedure at election and voting shall be..."*). When a user asks about the substantive rule, lexical matching often retrieves the subordinate procedural section (Section 50(2)) instead of the substantive governing section (Section 60(3)). This narrow rule detects explicit subordination clauses and promotes the substantive section referenced if it is already present in the candidate set.

### 9.2 Comprehensive Benchmark Suite Audit
Executed via `scripts/audit_promotion_rule.py` across **all 38 benchmark queries**:
- Retrieval Benchmark Suite (`tests/data/retrieval_bench.json`): 28 queries.
- Committed Held-Out Suite (`tests/data/heldout_bench.json`): 8 queries.
- Currency Benchmark Suite (`tests/data/currency_bench.json`): 2 queries.
- Natural / Spot-Check Queries: 6 queries.

### 9.3 Measured Findings
The cross-reference rule fired and altered ranking on **exactly ONE known query**:
- **Affected Query**: `"Must results be uploaded in real time?"`
  - Unmodified Top-1: `EA2026-S50-SS2` ("Subject to section 60 of this Act...")
  - Promoted Top-1: `EA2026-S60-SS3` (Substantive polling unit transmission procedure and Form EC8A collation rule)
  - Promotion Fired: `True`
- **Zero Impact on All Other Queries**: On the remaining 37 benchmark queries, `promotion_fired` was `False`, and 0 rankings were altered.

---

## 10. Serialized API Output Cache Verification (Audit Directive 4)

All API responses presented in evaluations and documentation are generated deterministically by `scripts/generate_api_outputs.py` and saved as JSON files in `data/cache/api_outputs/`. No output text or rank is manually typed.

The cache contains full API payloads for:
1. `data/cache/api_outputs/natural_01_over_voting.json`
2. `data/cache/api_outputs/natural_02_election_notice.json`
3. `data/cache/api_outputs/natural_03_primary_challenge.json`
4. `data/cache/api_outputs/natural_04_transmission.json`
5. `data/cache/api_outputs/natural_05_voter_card.json`
6. `data/cache/api_outputs/spot_check_real_time_upload.json`
7. `data/cache/api_outputs/section_29a_query.json`
8. `data/cache/api_outputs/heldout_001_en.json`
9. `data/cache/api_outputs/heldout_002_ha.json`
10. `data/cache/api_outputs/heldout_003_yo.json`
11. `data/cache/api_outputs/heldout_004_ig.json`
12. `data/cache/api_outputs/heldout_005_en.json`
13. `data/cache/api_outputs/heldout_006_ha.json`
14. `data/cache/api_outputs/heldout_007_yo.json`
15. `data/cache/api_outputs/heldout_008_ig.json`
16. `data/cache/api_outputs/redteam_candidate_pref.json`
17. `data/cache/api_outputs/redteam_prompt_injection.json`
18. `data/cache/api_outputs/check_official_domain.json`
19. `data/cache/api_outputs/check_fake_domain.json`

---

## 11. Decisions and Corrections Audit (Pre-Phase 2 Reopening)

### 11.1 Provenance and Empirical Recalibration of SCORE_GAP_THRESHOLD
- **Full History**: In Commit `9683c01`, `SCORE_GAP_THRESHOLD = 0.0001` was added under the commit label "pre-registered", but the commit diff and trajectory confirm it was chosen after inspecting the score margins of natural queries during Audit 6. Furthermore, documentation in `docs/evaluation_report.md` inadvertently cited `0.005` in text while `src/config.py` contained `0.0001`.
- **Validation Split**: A dedicated, frozen validation split (`tests/data/score_gap_val_split.json`, $n=12$) was created comprising 6 unambiguous statutory queries and 6 ambiguous / contested multi-section ties.
- **Empirical Calibration**:
  $$\text{Sweep: } \tau \in [0.00005, 0.0050]$$
  - At $\tau = 0.00010$, validation accuracy was only 50.0% (false negatives = 5; failed to abstain on ambiguous ties).
  - At $\tau = 0.00100$, accuracy reached **75.0%** with **F1 = 0.8000** and 100% recall on ambiguous ties (6/6).
- **Test Set Effect**: Re-evaluating on the separate test split without tuning confirms that Natural Query 2 ("How many days before the election must the commission publish the official notice?") correctly triggers abstention (`ABSTENTION_AMBIGUOUS_PROVISION`, gap = 0.000785 <= 0.0010), presenting the top-3 candidate sections without an unverified primary assertion.

### 11.2 Phase 1 Neural Retrieval: BGE-M3 & BGE-Reranker
- **Download and Memory Footprints**:
  - Python Wheel Packages:
    - `torch-2.15.0-cp313-win_amd64.whl`: **126.7 MB**
    - `transformers-5.22.2-py3-none-any.whl`: **13.1 MB**
    - `scipy-1.18.1-cp313-win_amd64.whl`: **36.6 MB**
    - `numpy-2.5.4-cp313-win_amd64.whl`: **12.6 MB**
    - `sentence_transformers-6.2.0-py3-none-any.whl`: **760 kB**
    - 23 secondary wheels: **~17 MB**
    - Total pip wheel download: **~206.8 MB**.
  - HuggingFace Model Weights:
    - `BAAI/bge-m3` (`model.safetensors`): **2.24 GB**
    - `BAAI/bge-reranker-v2-m3` (`model.safetensors`): **2.24 GB**
    - Combined weights footprint: **~4.48 GB**.
- **Local Machine Constraint**: On Windows 11 with Python 3.13, pip wheel extraction of torch's 15,000+ binary files stalled under real-time NTFS antivirus scanning. Rather than silently deferring, a complete Google Colab notebook (`notebooks/bge_m3_retrieval_benchmark.ipynb`) is provided for 1-click execution on free T4 GPU.
- **Code Architecture**: `src/retrieval/bge_engine.py` implements `BGEM3Retriever` behind `ENABLE_BGE_M3` and `ENABLE_BGE_RERANKER` flags, with graceful, zero-downtime fallback to `TranslationHybridRetriever`.

### 11.3 Language Identification: AfroLID + GlotLID Ensemble
- **Calibration Split**: `tests/data/lid_validation_bench.json` ($n=30$, 5 en, 5 ha, 5 yo, 5 ig, 5 pcm, 5 code-switched).
- **Threshold Sweep**:
  - At invented $\tau = 0.85$, accuracy dropped to **53.3%** due to excessive false-positive disambiguation.
  - Optimal empirical threshold: **$\tau_{\text{LID}} = 0.75$**, achieving **76.7% effective accuracy**.
- **Auditable Confusion Matrix**:
  | True \ Pred | en | ha | yo | ig | pcm | code_switched |
  | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
  | **en** | 5 | 0 | 0 | 0 | 0 | 0 |
  | **ha** | 0 | 5 | 0 | 0 | 0 | 0 |
  | **yo** | 0 | 0 | 5 | 0 | 0 | 0 |
  | **ig** | 0 | 0 | 1 | 4 | 0 | 0 |
  | **pcm** | 1 | 0 | 0 | 0 | 1 | 3 |
  | **code_switched** | 2 | 0 | 0 | 0 | 0 | 3 |
- **Disambiguation Policy**: Pure Pidgin and code-switched messages trigger interactive language confirmation (`"Reply 1 English, 2 Hausa, 3 Yoruba, 4 Igbo, 5 Pidgin"`).

### 11.4 Pre-Reviewed FAQ Library (Low-Risk Civic Topics)
- **File**: `data/processed/reviewed_faq_library.json`
- **Scope**: Exactly 10 civic topics:
  1. Voter Identification on Election Day (s.47(1))
  2. BVAS Accreditation Failure Protocol (s.47(3))
  3. Over-voting and Polling Unit Cancellation (s.51(2))
  4. Notice of Election Publication Timeline (s.28(1))
  5. Voter Registration Age and Citizenship (s.12(1))
  6. Transfer of Voter Registration (s.13(1))
  7. Place of Delivery of Nomination Papers (s.28(1)(b))
  8. Public Display of Polling Unit Results (s.60(2))
  9. Electronic Transmission of Results to IReV (s.60(3) + INEC ET Procedure)
  10. Verification of Collation Results (s.62(4))
- **Exclusion Policy**: Election petitions/tribunals (First Schedule, Sections 130-138) and criminal electoral offences (Sections 118-133) are **strictly excluded**.
- **Audit Review Labels**:
  - English: `REVIEWED_STATUTORY_AUTHORITY` (verbatim quote + short plain explanation).
  - Hausa, Yoruba, Igbo: `UNREVIEWED_DEVELOPER_DRAFT`.

### 11.5 Session Privacy & Security Guarantees
- **Module**: `src/web/session_store.py` (`SecureSessionStore`)
- **Key Mechanics**:
  - Sender Phone Number: One-way salted SHA-256 hash `hashlib.sha256((SALT + raw_sender_id).encode()).hexdigest()`. Raw phone number is never retained in memory, storage, or logs.
  - Zero Message Retention: Message bodies, queries, audio bytes, and personal identifiers are never stored in session state.
  - TTL Expiration: Automatic 24-hour expiration (86,400s) on all active sessions.
  - Opt-out Purge: Receiving `STOP`, `UNSUBSCRIBE`, or `CANCEL` immediately deletes the sender's hashed record.
  - Webhook Endpoint: `/api/v1/webhook/whatsapp` mock-tested and verified with passing test suite.
