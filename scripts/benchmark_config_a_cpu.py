"""
Evaluate Config A (Lexical / BM25+Dense Proxy Baseline) on CPU across all 33 test queries:
- 20 retrieval benchmark queries (tests/data/retrieval_bench.json)
- 8 held-out queries (tests/data/heldout_bench.json)
- 5 natural queries (tests/test_spot_check.py)
Measures Top-1, Hit@3, MRR, Wilson 95% CIs, and per-query CPU latency.
"""

import json
import time
import math
from pathlib import Path
from src.retrieval.translate_hybrid import TranslationHybridRetriever

def wilson_ci(hits: int, n: int, z: float = 1.96):
    if n == 0:
        return 0.0, 0.0
    p = hits / n
    denom = 1.0 + (z**2) / n
    center = (p + (z**2) / (2.0 * n)) / denom
    half_width = (z * math.sqrt((p * (1.0 - p) / n) + ((z**2) / (4.0 * (n**2))))) / denom
    return max(0.0, center - half_width), min(1.0, center + half_width)

def main():
    base_dir = Path(__file__).resolve().parent.parent

    # 1. Load the 20 retrieval queries
    with open(base_dir / "tests" / "data" / "retrieval_bench.json", "r", encoding="utf-8") as f:
        retrieval_queries = json.load(f)

    # 2. Load the 8 held-out queries
    with open(base_dir / "tests" / "data" / "heldout_bench.json", "r", encoding="utf-8") as f:
        heldout_queries = json.load(f)

    # 3. Define the 5 natural queries
    natural_queries = [
        {
            "id": "NAT_01",
            "language": "en",
            "query": "What happens if more ballots are counted than accredited voters at a polling station?",
            "target_section": "51",
            "target_chunk_id": "EA2026-S51-SS2"
        },
        {
            "id": "NAT_02",
            "language": "en",
            "query": "How many days before the election must the commission publish the official notice?",
            "target_section": "28",
            "target_chunk_id": "EA2026-S28-SS1"
        },
        {
            "id": "NAT_03",
            "language": "en",
            "query": "Who is allowed to challenge the outcome of a political party primary election in court?",
            "target_section": "29",
            "target_chunk_id": "EA2026-S29-SS5"
        },
        {
            "id": "NAT_04",
            "language": "en",
            "query": "How are election scores sent from polling booths to the national portal?",
            "target_section": "60",
            "target_chunk_id": "EA2026-S60-SS3"
        },
        {
            "id": "NAT_05",
            "language": "en",
            "query": "Can I vote if I do not have my permanent voter card on election day?",
            "target_section": "47",
            "target_chunk_id": "EA2026-S47-SS1"
        }
    ]

    all_queries = []
    for q in retrieval_queries:
        all_queries.append({"suite": "retrieval", **q})
    for q in heldout_queries:
        all_queries.append({"suite": "heldout", **q})
    for q in natural_queries:
        all_queries.append({"suite": "natural", **q})

    print(f"Total test queries assembled: {len(all_queries)} (20 retrieval + 8 heldout + 5 natural)")

    retriever = TranslationHybridRetriever(enable_online_translation=False, cache_enabled=True)

    latencies_ms = []
    results = []
    hits_at_1 = 0
    hits_at_3 = 0
    mrr_sum = 0.0

    for item in all_queries:
        qid = item["id"]
        q = item["query"]
        lang = item["language"]
        target_sec = str(item.get("target_section", ""))
        target_chunk = item.get("target_chunk_id", "")

        t0 = time.perf_counter()
        retrieved = retriever.retrieve(q, top_k=5, lang=lang)
        lat = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(lat)

        ret_secs = [str(c[0].section_number) for c in retrieved]
        ret_chunks = [c[0].chunk_id for c in retrieved]

        # Determine target rank
        rank = None
        for r_idx, (sec, cid) in enumerate(zip(ret_secs, ret_chunks), start=1):
            if (target_chunk and cid == target_chunk) or (target_sec and sec == target_sec):
                rank = r_idx
                break

        hit1 = (rank == 1)
        hit3 = (rank is not None and rank <= 3)

        if hit1:
            hits_at_1 += 1
        if hit3:
            hits_at_3 += 1
        if rank:
            mrr_sum += 1.0 / rank

        results.append({
            "id": qid,
            "suite": item["suite"],
            "language": lang,
            "query": q,
            "target_section": target_sec,
            "target_chunk_id": target_chunk,
            "retrieved_sections": ret_secs,
            "retrieved_chunk_ids": ret_chunks,
            "rank": rank,
            "hit1": hit1,
            "hit3": hit3,
            "latency_ms": round(lat, 2)
        })

    n = len(all_queries)
    top1_rate = hits_at_1 / n
    hit3_rate = hits_at_3 / n
    mrr = mrr_sum / n
    avg_lat = sum(latencies_ms) / n

    top1_ci = wilson_ci(hits_at_1, n)
    hit3_ci = wilson_ci(hits_at_3, n)

    print("\n=====================================================================")
    print("CONFIG A: LEXICAL (BM25 + DENSE PROXY) BASELINE RESULTS (CPU)")
    print(f"Total Queries (N): {n}")
    print(f"Top-1 Accuracy:    {top1_rate:.1%} ({hits_at_1}/{n}) [95% CI: {top1_ci[0]:.1%} - {top1_ci[1]:.1%}]")
    print(f"Hit@3 Accuracy:    {hit3_rate:.1%} ({hits_at_3}/{n}) [95% CI: {hit3_ci[0]:.1%} - {hit3_ci[1]:.1%}]")
    print(f"MRR:               {mrr:.4f}")
    print(f"Mean CPU Latency:  {avg_lat:.2f} ms")
    print("=====================================================================")

    out_file = base_dir / "data" / "cache" / "config_a_cpu_baseline.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "config": "Config A: Lexical Baseline (BM25 + Dense Proxy)",
            "device": "CPU",
            "n_queries": n,
            "top1_accuracy": top1_rate,
            "top1_wilson_ci": top1_ci,
            "hit3_accuracy": hit3_rate,
            "hit3_wilson_ci": hit3_ci,
            "mrr": mrr,
            "mean_latency_ms": avg_lat,
            "detailed_results": results
        }, f, indent=2, ensure_ascii=False)
    print(f"Saved Config A CPU baseline results to {out_file}")

if __name__ == "__main__":
    main()

