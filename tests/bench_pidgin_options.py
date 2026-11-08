"""
Benchmark Nigerian Pidgin (pcm) Handling Strategies for Electoral Retrieval.
Evaluates three candidate options on frozen validation queries:
  Option (a): Direct pass-through to English retrieval.
  Option (b): Small curated rule-based / dictionary mapper.
  Option (c): Abstain with a polite message (Hit@3 = 0.0%).
"""

import json
from pathlib import Path
from src.retrieval.translate_hybrid import TranslationHybridRetriever

def main():
    bench_path = Path(__file__).resolve().parent / "data" / "lid_validation_bench.json"
    with open(bench_path, "r", encoding="utf-8") as f:
        bench_data = json.load(f)

    pcm_targets = {
        "LID_VAL_21": "47",
        "LID_VAL_22": "51",
        "LID_VAL_23": "28",
        "LID_VAL_24": "12",
        "LID_VAL_25": "60"
    }

    pcm_queries = [item for item in bench_data if item["id"] in pcm_targets]

    retriever = TranslationHybridRetriever(enable_online_translation=False)

    print("=====================================================================")
    print("NIGERIAN PIDGIN (pcm) RETRIEVAL STRATEGY BENCHMARK")
    print(f"Total Pidgin validation queries: {len(pcm_queries)}")
    print("=====================================================================\n")

    # OPTION A: Direct pass-through
    print("--- Option (a): Direct Pass-Through to English Retrieval ---")
    hits_a = 0
    results_a = []
    for item in pcm_queries:
        qid = item["id"]
        query = item["text"]
        target = pcm_targets[qid]
        res = retriever.retrieve(query, top_k=3, lang="en")
        sections = [r[0].section_number for r in res]
        hit = target in sections
        if hit:
            hits_a += 1
        rank = (sections.index(target) + 1) if hit else None
        results_a.append({"id": qid, "query": query, "target": target, "retrieved": sections, "hit": hit, "rank": rank})
        print(f"  [{qid}] Target: S.{target} | Retrieved: {[f'S.{s}' for s in sections]} | Hit@3: {hit} (Rank: {rank})")

    hit3_a = hits_a / len(pcm_queries)
    print(f"Option (a) Hit@3: {hits_a}/{len(pcm_queries)} = {hit3_a:.1%}\n")

    # OPTION B: Curated rule-based dictionary mapper
    # Civic mapping for Nigerian Pidgin legal/procedural terms
    pcm_civic_dict = {
        "i fit": "can i",
        "no carry": "without do not have",
        "pvc": "permanent voter card",
        "polling unit": "polling unit",
        "wetin go happen": "what happens",
        "vote plenty pass": "over-voting votes exceed accredited voters",
        "bvas scan": "bvas accreditation",
        "suppose give": "publish notice of election",
        "which age": "minimum age 18 years",
        "shey": "",
        "presiding officer": "presiding officer",
        "dey transmit": "electronically transmit upload",
        "straight to irev": "irev portal election results"
    }

    def map_pcm_query(text: str) -> str:
        lowered = text.lower()
        expansions = []
        for phrase, eng in pcm_civic_dict.items():
            if phrase in lowered and eng:
                expansions.append(eng)
        if expansions:
            return text + " " + " ".join(expansions)
        return text

    print("--- Option (b): Curated Rule-Based / Dictionary Mapper ---")
    hits_b = 0
    results_b = []
    for item in pcm_queries:
        qid = item["id"]
        query = item["text"]
        target = pcm_targets[qid]
        expanded_q = map_pcm_query(query)
        res = retriever.retrieve(expanded_q, top_k=3, lang="en")
        sections = [r[0].section_number for r in res]
        hit = target in sections
        if hit:
            hits_b += 1
        rank = (sections.index(target) + 1) if hit else None
        results_b.append({"id": qid, "query": query, "mapped": expanded_q, "target": target, "retrieved": sections, "hit": hit, "rank": rank})
        print(f"  [{qid}] Target: S.{target} | Retrieved: {[f'S.{s}' for s in sections]} | Hit@3: {hit} (Rank: {rank})")

    hit3_b = hits_b / len(pcm_queries)
    print(f"Option (b) Hit@3: {hits_b}/{len(pcm_queries)} = {hit3_b:.1%}\n")

    # OPTION C: Abstain with polite message
    print("--- Option (c): Abstain with Polite Disambiguation Notice ---")
    print("  All queries trigger immediate polite abstention.")
    hit3_c = 0.0
    print(f"Option (c) Hit@3: 0/{len(pcm_queries)} = {hit3_c:.1%}\n")

    # Save benchmark results
    out_path = Path(__file__).resolve().parent.parent / "data" / "cache" / "pidgin_strategy_benchmark.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "num_queries": len(pcm_queries),
            "option_a_direct_passthrough": {
                "hit3": hit3_a,
                "hits": hits_a,
                "details": results_a
            },
            "option_b_rule_mapped": {
                "hit3": hit3_b,
                "hits": hits_b,
                "details": results_b
            },
            "option_c_abstain": {
                "hit3": hit3_c,
                "hits": 0,
                "details": []
            }
        }, f, indent=2, ensure_ascii=False)
    print(f"Saved benchmark results to {out_path}")

if __name__ == "__main__":
    main()
