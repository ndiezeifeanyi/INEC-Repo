"""
Export full official corpus (514 chunks) and frozen 33 test queries
for the Colab comparison benchmark across Configs A, B, C, D, E.
"""

import json
from pathlib import Path

def main():
    base_dir = Path(__file__).resolve().parent.parent

    # 1. Load full 514 corpus chunks
    corpus_chunks = []
    files = [
        base_dir / "data" / "processed" / "electoral_act_2026.jsonl",
        base_dir / "data" / "processed" / "inec_transmission_procedure.jsonl"
    ]
    for f in files:
        if f.exists():
            with open(f, "r", encoding="utf-8") as fh:
                for line in fh:
                    if line.strip():
                        corpus_chunks.append(json.loads(line))

    print(f"Loaded {len(corpus_chunks)} official corpus chunks.")

    # 2. Load 33 test queries
    with open(base_dir / "tests" / "data" / "retrieval_bench.json", "r", encoding="utf-8") as f:
        retrieval_queries = json.load(f)

    with open(base_dir / "tests" / "data" / "heldout_bench.json", "r", encoding="utf-8") as f:
        heldout_queries = json.load(f)

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

    print(f"Assembled {len(all_queries)} frozen benchmark queries.")

    # Export to processed files
    out_corpus = base_dir / "data" / "processed" / "full_corpus_for_embedding.json"
    with open(out_corpus, "w", encoding="utf-8") as f:
        json.dump(corpus_chunks, f, indent=2, ensure_ascii=False)
    print(f"Exported corpus to {out_corpus}")

    out_queries = base_dir / "data" / "processed" / "benchmark_queries_33.json"
    with open(out_queries, "w", encoding="utf-8") as f:
        json.dump(all_queries, f, indent=2, ensure_ascii=False)
    print(f"Exported queries to {out_queries}")

if __name__ == "__main__":
    main()

