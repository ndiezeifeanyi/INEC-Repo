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

def evaluate_set(retriever, query_list, enable_online=False, label=""):
    hits_at_3 = 0
    mrr_sum = 0.0
    details = []

    for item in query_list:
        lang = item["language"]
        q = item["query"]
        target_sec = item.get("target_section")
        target_chunk = item.get("target_chunk_id")

        retrieved = retriever.retrieve(q, top_k=5, lang=lang, allow_online=enable_online)
        ret_secs = [c[0].section_number for c in retrieved]
        ret_chunks = [c[0].chunk_id for c in retrieved]

        hit = False
        if target_sec and target_sec in ret_secs[:3]:
            hit = True
        elif target_chunk and target_chunk in ret_chunks[:3]:
            hit = True

        if hit:
            hits_at_3 += 1

        rank = None
        if target_sec and target_sec in ret_secs:
            rank = ret_secs.index(target_sec) + 1
        elif target_chunk and target_chunk in ret_chunks:
            rank = ret_chunks.index(target_chunk) + 1

        if rank is not None:
            mrr_sum += 1.0 / rank

        en_translated = retriever.translate_query_to_english(q, lang, allow_online=enable_online)
        details.append({
            "id": item.get("id"),
            "lang": lang,
            "query": q,
            "translated_to_en": en_translated,
            "target": target_sec or target_chunk,
            "top3_retrieved": ret_chunks[:3],
            "hit@3": hit,
            "rank": rank
        })

    n = len(query_list)
    p = hits_at_3 / n if n else 0
    ci_lower, ci_upper = calculate_wilson_ci(hits_at_3, n)
    mrr = mrr_sum / n if n else 0

    return {
        "set_label": label,
        "n_samples": n,
        "hits_at_3": hits_at_3,
        "recall@3": f"{p*100:.1f}% ({hits_at_3}/{n})",
        "recall@3_wilson_95ci": f"[{ci_lower*100:.1f}%, {ci_upper*100:.1f}%]",
        "mrr": f"{mrr:.3f}",
        "details": details
    }

# 1. Current committed held-out benchmark (tests/data/heldout_bench.json)
with open("tests/data/heldout_bench.json", "r", encoding="utf-8") as f:
    committed_heldout = json.load(f)

# 2. Original held-out benchmark from commit d026f78 (items 5-8 targeted deleted guideline section 18)
with open("tests/data/heldout_bench.json", "r", encoding="utf-8") as f:
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

# 3. Audit 5 exploratory queries (used in run_heldout_real_trans.py)
audit5_variant_queries = [
    {
        "id": "variant_001_s51",
        "language": "yo",
        "query": "Kini yoo sele ti iye ibo ti a di ni ibudo ibo ba ju iye awon oludibo ti a se afihan won lo?",
        "target_section": "51"
    },
    {
        "id": "variant_002_s51",
        "language": "ig",
        "query": "Gini na-eme ma obu na vootu a turu n'otu ebe vootu kariri onu ogugu ndi mmadu enyochara akwukwo ha?",
        "target_section": "51"
    },
    {
        "id": "variant_003_s12",
        "language": "ha",
        "query": "Wane shekaru ne mutum zai iya yin rajistar zabe a Najeriya?",
        "target_section": "12"
    },
    {
        "id": "variant_004_s12",
        "language": "yo",
        "query": "Ojo ori melo ni o ye ki eniyan to ki o to le forukosile lati dibo?",
        "target_section": "12"
    },
    {
        "id": "variant_005_s12",
        "language": "ig",
        "query": "Afọ ole ka mmadụ ga-adị tupu o nwee ike idebanye aha maka vootu?",
        "target_section": "12"
    }
]

retriever = TranslationHybridRetriever()

# Run Set 1: Committed held-out (Offline mode)
res_committed_offline = evaluate_set(retriever, committed_heldout, enable_online=False, label="Committed Held-out (Offline Mode)")

# Run Set 2: Committed held-out (Online gtx endpoint mode)
res_committed_online = evaluate_set(retriever, committed_heldout, enable_online=True, label="Committed Held-out (gtx Online Mode)")

# Run Set 3: d026f78 original held-out (Offline mode)
res_d026f78_offline = evaluate_set(retriever, d026f78_heldout, enable_online=False, label="d026f78 Original Queries (Offline Mode)")

# Run Set 4: d026f78 original held-out (Online gtx endpoint mode)
res_d026f78_online = evaluate_set(retriever, d026f78_heldout, enable_online=True, label="d026f78 Original Queries (gtx Online Mode)")

# Run Set 5: Audit 5 variant queries (Online gtx mode)
res_audit5_variant = evaluate_set(retriever, audit5_variant_queries, enable_online=True, label="Audit 5 Exploratory Variants (gtx Online Mode)")

output = {
    "committed_offline": res_committed_offline,
    "committed_online": res_committed_online,
    "d026f78_offline": res_d026f78_offline,
    "d026f78_online": res_d026f78_online,
    "audit5_variant": res_audit5_variant
}

with open("data/cache/heldout_audit6_results.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print("SUCCESS: Heldout Audit 6 benchmarks computed.")

