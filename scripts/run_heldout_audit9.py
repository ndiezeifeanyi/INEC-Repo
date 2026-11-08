import json
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.retrieval.translate_hybrid import TranslationHybridRetriever

def calculate_wilson_ci(hits: int, total: int, z: float = 1.96):
    if total == 0:
        return 0.0, 0.0
    p = hits / total
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2.0 * total)) / denom
    half_width = (z * math.sqrt((p * (1.0 - p) / total) + ((z**2) / (4.0 * (total**2))))) / denom
    lower = max(0.0, center - half_width)
    upper = min(1.0, center + half_width)
    return lower, upper

def evaluate_set(retriever, query_list, enable_online=False, cache_enabled=True, label=""):
    hits_at_1 = 0
    hits_at_3 = 0
    mrr_sum = 0.0
    details = []

    for item in query_list:
        lang = item["language"]
        q = item["query"]
        target_sec = item.get("target_section")
        target_chunk = item.get("target_chunk_id")

        retrieved = retriever.retrieve(
            q, top_k=5, lang=lang, allow_online=enable_online, cache_enabled=cache_enabled
        )
        ret_secs = [c[0].section_number for c in retrieved]
        ret_chunks = [c[0].chunk_id for c in retrieved]

        # Top-1 Hit
        hit_1 = False
        if target_sec and ret_secs and target_sec == ret_secs[0]:
            hit_1 = True
        elif target_chunk and ret_chunks and target_chunk == ret_chunks[0]:
            hit_1 = True

        if hit_1:
            hits_at_1 += 1

        # Hit@3
        hit_3 = False
        if target_sec and target_sec in ret_secs[:3]:
            hit_3 = True
        elif target_chunk and target_chunk in ret_chunks[:3]:
            hit_3 = True

        if hit_3:
            hits_at_3 += 1

        rank = None
        if target_sec and target_sec in ret_secs:
            rank = ret_secs.index(target_sec) + 1
        elif target_chunk and target_chunk in ret_chunks:
            rank = ret_chunks.index(target_chunk) + 1

        if rank is not None:
            mrr_sum += 1.0 / rank

        en_translated = retriever.translate_query_to_english(
            q, lang, allow_online=enable_online, cache_enabled=cache_enabled
        )
        details.append({
            "id": item.get("id"),
            "lang": lang,
            "query": q,
            "translated_to_en": en_translated,
            "target": target_sec or target_chunk,
            "top3_retrieved": ret_chunks[:3],
            "top3_sections": ret_secs[:3],
            "bm25_top1": getattr(retrieved, "bm25_top1", None),
            "dense_top1": getattr(retrieved, "dense_top1", None),
            "bm25_dense_disagree": getattr(retrieved, "bm25_dense_disagree", False),
            "hit@1": hit_1,
            "hit@3": hit_3,
            "rank": rank
        })

    n = len(query_list)
    p1 = hits_at_1 / n if n else 0.0
    p3 = hits_at_3 / n if n else 0.0
    ci1_lower, ci1_upper = calculate_wilson_ci(hits_at_1, n)
    ci3_lower, ci3_upper = calculate_wilson_ci(hits_at_3, n)
    mrr = mrr_sum / n if n else 0.0

    return {
        "set_label": label,
        "n_samples": n,
        "hits_at_1": hits_at_1,
        "recall@1": f"{p1*100:.1f}% ({hits_at_1}/{n})",
        "recall@1_wilson_95ci": f"[{ci1_lower*100:.1f}%, {ci1_upper*100:.1f}%]",
        "hits_at_3": hits_at_3,
        "recall@3": f"{p3*100:.1f}% ({hits_at_3}/{n})",
        "recall@3_wilson_95ci": f"[{ci3_lower*100:.1f}%, {ci3_upper*100:.1f}%]",
        "mrr": f"{mrr:.3f}",
        "details": details
    }

def main():
    base_dir = Path(__file__).resolve().parent.parent

    # 1. Current committed held-out benchmark (tests/data/heldout_bench.json)
    with open(base_dir / "tests" / "data" / "heldout_bench.json", "r", encoding="utf-8") as f:
        committed_heldout = json.load(f)

    # 2. Original held-out benchmark from commit d026f78 (items 5-8 targeted deleted guideline section 18)
    with open(base_dir / "tests" / "data" / "heldout_bench.json", "r", encoding="utf-8") as f:
        d026f78_heldout = json.load(f)[:4] + [
            {
                "id": "heldout_005_d026f78",
                "language": "en",
                "query": "At what time does accreditation and voting commence and close at polling stations?",
                "target_doc": "INEC Regulations and Guidelines 2026 (DELETED/UNGROUNDED)",
                "target_section": "18",
                "target_chunk_id": "INEC2026-REG-S18-SS1"
            },
            {
                "id": "heldout_006_d026f78",
                "language": "ha",
                "query": "Wane lokaci ake fara tantancewa da kada kuri'a sannan a wane lokaci ake rufewa?",
                "target_doc": "INEC Regulations and Guidelines 2026 (DELETED/UNGROUNDED)",
                "target_section": "18",
                "target_chunk_id": "INEC2026-REG-S18-SS1"
            },
            {
                "id": "heldout_007_d026f78",
                "language": "yo",
                "query": "Agogo melo ni a n bere ijeri ati idibo ti a si n pari re ni ibudo ibo?",
                "target_doc": "INEC Regulations and Guidelines 2026 (DELETED/UNGROUNDED)",
                "target_section": "18",
                "target_chunk_id": "INEC2026-REG-S18-SS1"
            },
            {
                "id": "heldout_008_d026f78",
                "language": "ig",
                "query": "Oge ole ka a na-ebido nzere na itu vootu nakwa oge ole ka a na-emechi ya?",
                "target_doc": "INEC Regulations and Guidelines 2026 (DELETED/UNGROUNDED)",
                "target_section": "18",
                "target_chunk_id": "INEC2026-REG-S18-SS1"
            }
        ]

    # 3. Natural queries set
    natural_queries = [
        {
            "id": "natural_001_over_voting",
            "language": "en",
            "query": "What happens if more ballots are counted than accredited voters at a polling station?",
            "target_section": "51"
        },
        {
            "id": "natural_002_election_notice",
            "language": "en",
            "query": "How many days before the election must the commission publish the official notice?",
            "target_section": "28"
        },
        {
            "id": "natural_003_primary_challenge",
            "language": "en",
            "query": "Who is allowed to challenge the outcome of a political party primary election in court?",
            "target_section": "29"
        },
        {
            "id": "natural_004_transmission",
            "language": "en",
            "query": "How are election scores sent from polling booths to the national portal?",
            "target_section": "60"
        },
        {
            "id": "natural_005_voter_card",
            "language": "en",
            "query": "Can I vote if I do not have my permanent voter card on election day?",
            "target_section": "47"
        },
        {
            "id": "natural_006_real_time_upload",
            "language": "en",
            "query": "Must results be uploaded in real time?",
            "target_section": "60"
        }
    ]

    retriever = TranslationHybridRetriever()

    # 1. Committed Held-Out: dictionary only mode
    res_committed_dict = evaluate_set(
        retriever, committed_heldout,
        enable_online=False, cache_enabled=False,
        label="Committed Held-out (dictionary only)"
    )

    # 2. Committed Held-Out: dictionary + cached online translation mode
    res_committed_cached = evaluate_set(
        retriever, committed_heldout,
        enable_online=True, cache_enabled=True,
        label="Committed Held-out (dictionary + cached online translation)"
    )

    # 3. d026f78 Original Held-Out: dictionary only mode
    res_d026f78_dict = evaluate_set(
        retriever, d026f78_heldout,
        enable_online=False, cache_enabled=False,
        label="d026f78 Original Held-out (dictionary only)"
    )

    # 4. d026f78 Original Held-Out: dictionary + cached online translation mode
    res_d026f78_cached = evaluate_set(
        retriever, d026f78_heldout,
        enable_online=True, cache_enabled=True,
        label="d026f78 Original Held-out (dictionary + cached online translation)"
    )

    # 5. Natural queries set (English)
    res_natural = evaluate_set(
        retriever, natural_queries,
        enable_online=False, cache_enabled=False,
        label="Natural English Queries (No Section Jargon)"
    )

    output = {
        "committed_dictionary_only": res_committed_dict,
        "committed_cached_online": res_committed_cached,
        "d026f78_dictionary_only": res_d026f78_dict,
        "d026f78_cached_online": res_d026f78_cached,
        "natural_queries": res_natural
    }

    out_file = base_dir / "data" / "cache" / "heldout_audit9_results.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"SUCCESS: Heldout Audit 9 benchmarks computed and saved to {out_file}.")

if __name__ == "__main__":
    main()
