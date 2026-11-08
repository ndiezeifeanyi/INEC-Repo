import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.retrieval.translate_hybrid import TranslationHybridRetriever, reciprocal_rank_fusion

base_dir = Path(__file__).resolve().parent.parent
retriever = TranslationHybridRetriever()

# Collect all queries from all benchmark suites
all_test_queries = []

# 1. Retrieval benchmark (28 queries)
with open(base_dir / "tests" / "data" / "retrieval_bench.json", "r", encoding="utf-8") as f:
    for item in json.load(f):
        all_test_queries.append(("retrieval_bench", item["id"], item["query"], item["language"]))

# 2. Committed held-out benchmark (8 queries)
with open(base_dir / "tests" / "data" / "heldout_bench.json", "r", encoding="utf-8") as f:
    for item in json.load(f):
        all_test_queries.append(("heldout_bench", item["id"], item["query"], item["language"]))

# 3. Currency benchmark (2 queries)
with open(base_dir / "tests" / "data" / "currency_bench.json", "r", encoding="utf-8") as f:
    for item in json.load(f):
        all_test_queries.append(("currency_bench", item["id"], item["query"], item.get("language", "en")))

# 4. Spot check & Natural queries (6 queries)
natural = [
    ("natural_1", "What happens if more ballots are counted than accredited voters at a polling station?", "en"),
    ("natural_2", "How many days before the election must the commission publish the official notice?", "en"),
    ("natural_3", "Who is allowed to challenge the outcome of a political party primary election in court?", "en"),
    ("natural_4", "How are election scores sent from polling booths to the national portal?", "en"),
    ("natural_5", "Can I vote if I do not have my permanent voter card on election day?", "en"),
    ("spot_check_real_time", "Must results be uploaded in real time?", "en")
]
for sid, q, l in natural:
    all_test_queries.append(("natural_queries", sid, q, l))

print(f"Total queries to evaluate: {len(all_test_queries)}")

changed_queries = []

for suite, qid, query, lang in all_test_queries:
    en_query = retriever.translate_query_to_english(query, lang, allow_online=True)

    # BM25 + Dense
    q_set = set(retriever._tokenize(en_query))
    dense_scores = []
    for chunk in retriever.chunks:
        doc_tokens = set(retriever._tokenize(f"{chunk.content_english} {chunk.content_plain} {chunk.section_number}"))
        overlap = len(q_set.intersection(doc_tokens))
        if overlap > 0:
            dense_scores.append((chunk, float(overlap) / (len(q_set) + 1)))
    dense_scores.sort(key=lambda x: x[1], reverse=True)
    bm25_scores = retriever._bm25_score(en_query)

    # Raw RRF without promotion rule
    fused_unmodified = reciprocal_rank_fusion([bm25_scores, dense_scores])

    # Fused with promotion rule
    fused_promoted = list(fused_unmodified)
    promotion_fired = False
    if fused_promoted:
        top_c = fused_promoted[0][0]
        m = re.match(r"^Subject to section (\d+)", top_c.content_english.strip(), re.IGNORECASE)
        if m:
            target_sec = m.group(1)
            for idx, (c, sc) in enumerate(fused_promoted[1:], start=1):
                if c.section_number == target_sec:
                    promoted_chunk = fused_promoted.pop(idx)
                    fused_promoted.insert(0, (promoted_chunk[0], fused_promoted[0][1] + 0.001))
                    promotion_fired = True
                    break

    unmodified_top1 = fused_unmodified[0][0].chunk_id if fused_unmodified else None
    promoted_top1 = fused_promoted[0][0].chunk_id if fused_promoted else None

    if promotion_fired or unmodified_top1 != promoted_top1:
        changed_queries.append({
            "suite": suite,
            "id": qid,
            "query": query,
            "lang": lang,
            "unmodified_top1": unmodified_top1,
            "promoted_top1": promoted_top1,
            "promotion_fired": promotion_fired
        })

print(f"\nQueries where promotion rule fired or changed top-1: {len(changed_queries)}")
for c in changed_queries:
    print(json.dumps(c, indent=2))
