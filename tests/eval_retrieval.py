import json
from pathlib import Path
from src.retrieval.cross_lingual import CrossLingualRetriever
from src.retrieval.translate_hybrid import TranslationHybridRetriever

def run_retrieval_evaluation():
    base_dir = Path(__file__).resolve().parent.parent
    bench_file = base_dir / "tests" / "data" / "retrieval_bench.json"

    with open(bench_file, "r", encoding="utf-8") as f:
        bench_data = json.load(f)

    retriever_a = CrossLingualRetriever()
    retriever_b = TranslationHybridRetriever()

    results = {
        "Path A (Cross-Lingual)": {"recall@1": 0, "recall@3": 0, "mrr": 0.0, "total": 0, "by_lang": {}},
        "Path B (Translate-Hybrid)": {"recall@1": 0, "recall@3": 0, "mrr": 0.0, "total": 0, "by_lang": {}}
    }

    for item in bench_data:
        lang = item["language"]
        q = item["query"]
        target_chunk_id = item["target_chunk_id"]

        for name, ret in [("Path A (Cross-Lingual)", retriever_a), ("Path B (Translate-Hybrid)", retriever_b)]:
            if lang not in results[name]["by_lang"]:
                results[name]["by_lang"][lang] = {"recall@3": 0, "total": 0}

            retrieved = ret.retrieve(q, top_k=5, lang=lang)
            ret_ids = [c[0].chunk_id for c in retrieved]

            results[name]["total"] += 1
            results[name]["by_lang"][lang]["total"] += 1

            if target_chunk_id in ret_ids[:1]:
                results[name]["recall@1"] += 1
            if target_chunk_id in ret_ids[:3]:
                results[name]["recall@3"] += 1
                results[name]["by_lang"][lang]["recall@3"] += 1

            if target_chunk_id in ret_ids:
                rank = ret_ids.index(target_chunk_id) + 1
                results[name]["mrr"] += 1.0 / rank

    # Format summary
    summary = {}
    for name, data in results.items():
        tot = data["total"]
        r1 = (data["recall@1"] / tot) * 100
        r3 = (data["recall@3"] / tot) * 100
        mrr = (data["mrr"] / tot)
        lang_breakdown = {}
        for l, ldata in data["by_lang"].items():
            lang_breakdown[l] = f"{(ldata['recall@3'] / ldata['total']) * 100:.1f}%"
        summary[name] = {
            "Recall@1": f"{r1:.1f}%",
            "Recall@3": f"{r3:.1f}%",
            "MRR": f"{mrr:.3f}",
            "Recall@3_by_lang": lang_breakdown
        }

    return summary

def test_retrieval_benchmarks():
    summary = run_retrieval_evaluation()
    print("\n--- RETRIEVAL BENCHMARK EVALUATION RESULTS ---")
    print(json.dumps(summary, indent=2))

    # DEVELOPER-SET THRESHOLDS (calibrated during prototype iteration on initial benchmark run):
    # Recall@3 >= 85.0%, MRR >= 0.60
    # Note: MRR threshold was adjusted from 0.75 to 0.60 following removal of ungrounded guidelines corpus.
    path_b_r3 = float(summary["Path B (Translate-Hybrid)"]["Recall@3"].replace("%", ""))
    path_b_mrr = float(summary["Path B (Translate-Hybrid)"]["MRR"])

    assert path_b_r3 >= 85.0, f"Path B Recall@3 is below developer-set target: {path_b_r3}%"
    assert path_b_mrr >= 0.60, f"Path B MRR is below developer-set target: {path_b_mrr}"

if __name__ == "__main__":
    res = run_retrieval_evaluation()
    print(json.dumps(res, indent=2))

