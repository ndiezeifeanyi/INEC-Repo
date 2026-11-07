import json
import math
from pathlib import Path
from src.retrieval.translate_hybrid import TranslationHybridRetriever

def calculate_wilson_score_interval(hits: int, total: int, z: float = 1.96):
    """
    Computes the Wilson score interval for a binomial proportion.
    More robust than normal approximation for small sample sizes or extreme proportions.
    """
    if total == 0:
        return 0.0, 0.0
    p = hits / total
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2.0 * total)) / denom
    half_width = (z * math.sqrt((p * (1.0 - p) / total) + ((z**2) / (4.0 * (total**2))))) / denom
    lower = max(0.0, center - half_width)
    upper = min(1.0, center + half_width)
    return lower, upper

def run_heldout_evaluation():
    base_dir = Path(__file__).resolve().parent.parent
    bench_file = base_dir / "tests" / "data" / "heldout_bench.json"

    with open(bench_file, "r", encoding="utf-8") as f:
        bench_data = json.load(f)

    retriever = TranslationHybridRetriever()
    n = len(bench_data)
    hits_at_3 = 0
    mrr_sum = 0.0

    by_lang = {}

    for item in bench_data:
        lang = item["language"]
        q = item["query"]
        target_sec = item["target_section"]

        if lang not in by_lang:
            by_lang[lang] = {"hits_at_3": 0, "total": 0}
        by_lang[lang]["total"] += 1

        retrieved = retriever.retrieve(q, top_k=5, lang=lang)
        ret_secs = [c[0].section_number for c in retrieved]

        if target_sec in ret_secs[:3]:
            hits_at_3 += 1
            by_lang[lang]["hits_at_3"] += 1

        if target_sec in ret_secs:
            rank = ret_secs.index(target_sec) + 1
            mrr_sum += 1.0 / rank

    p = hits_at_3 / n
    ci_lower, ci_upper = calculate_wilson_score_interval(hits_at_3, n, z=1.96)
    mrr = mrr_sum / n

    # Audit Rule: Do not report per-language rates below n=20 threshold
    by_lang_report = {}
    for l, d in by_lang.items():
        if d["total"] < 20:
            by_lang_report[l] = f"SUPPRESSED (n={d['total']} < 20 threshold: statistical sample too small)"
        else:
            by_lang_report[l] = f"{(d['hits_at_3']/d['total'])*100:.1f}% (n={d['total']})"

    report = {
        "n_samples": n,
        "query_provenance": "Authored by developer test author (synthetic voter prompts, held out from index design)",
        "recall@3": f"{p*100:.1f}%",
        "recall@3_wilson_95ci": f"[{ci_lower*100:.1f}%, {ci_upper*100:.1f}%]",
        "mrr": f"{mrr:.3f}",
        "by_language": by_lang_report,
        "circularity_disclosure": (
            "WARNING / CIRCULARITY NOTE: In Path B, queries containing terms explicitly mapped in the translation "
            "layer benefit from direct keyword alignment with the statutory index. On the held-out set where terms "
            "are not verbatim in the unreviewed glossary, performance reflects pure lexical and morphological overlap. "
            "Native reviewer audits are required to eliminate remaining circularity."
        )
    }

    print("\n--- HELD-OUT BENCHMARK EVALUATION ---")
    print(json.dumps(report, indent=2))
    return report

def test_heldout_suite():
    res = run_heldout_evaluation()
    assert res["n_samples"] == 8
    assert "wilson" in res["recall@3_wilson_95ci"].lower() or "[" in res["recall@3_wilson_95ci"]
    assert "circularity_disclosure" in res
    for l, status in res["by_language"].items():
        assert "SUPPRESSED" in status

if __name__ == "__main__":
    run_heldout_evaluation()
