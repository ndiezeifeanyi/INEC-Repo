import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retrieval.translate_hybrid import TranslationHybridRetriever
from src.generation.prompt_builder import GroundedAnswerGenerator
from src.config import SCORE_GAP_THRESHOLD, ELECTORAL_OFFENCES_SECTION_RANGE

def main():
    retriever = TranslationHybridRetriever()
    generator = GroundedAnswerGenerator()

    natural_queries = [
        ("Natural 1 (Over-voting)", "What happens if more ballots are counted than accredited voters at a polling station?", "en"),
        ("Natural 2 (Election Notice)", "How many days before the election must the commission publish the official notice?", "en"),
        ("Natural 3 (Primary Challenge)", "Who is allowed to challenge the outcome of a political party primary election in court?", "en"),
        ("Natural 4 (Transmission)", "How are election scores sent from polling booths to the national portal?", "en"),
        ("Natural 5 (Voter Card)", "Can I vote if I do not have my permanent voter card on election day?", "en"),
        ("Natural 6 (Real Time Upload)", "Must results be uploaded in real time?", "en"),
    ]

    with open("tests/data/heldout_bench.json", "r", encoding="utf-8") as f:
        heldout = json.load(f)

    queries = []
    for item in heldout:
        queries.append((f"Heldout {item['id']} ({item['language']})", item["query"], item["language"]))

    all_queries = natural_queries + queries

    print(f"=== EVALUATING {len(all_queries)} QUERIES FOR SCORES, GAPS, AND ABSTENTION ===")
    print(f"Config SCORE_GAP_THRESHOLD: {SCORE_GAP_THRESHOLD}")
    print(f"Config ELECTORAL_OFFENCES_RANGE: {ELECTORAL_OFFENCES_SECTION_RANGE}\n")

    results = []

    for label, q, lang in all_queries:
        res = retriever.retrieve(q, top_k=3, lang=lang)
        top1_id = res[0][0].chunk_id if len(res) > 0 else "NONE"
        top1_sc = res[0][1] if len(res) > 0 else 0.0
        top2_id = res[1][0].chunk_id if len(res) > 1 else "NONE"
        top2_sc = res[1][1] if len(res) > 1 else 0.0
        gap = top1_sc - top2_sc

        ans = generator.generate_answer(q, res, lang=lang)
        abstained = "ABSTENTION_AMBIGUOUS_PROVISION" in ans.confidence_flags or "ABSTENTION_UNSUPPORTED_RETRIEVAL" in ans.confidence_flags

        res_obj = {
            "label": label,
            "query": q,
            "language": lang,
            "top1_id": top1_id,
            "top1_score": round(top1_sc, 6),
            "top2_id": top2_id,
            "top2_score": round(top2_sc, 6),
            "score_gap": round(gap, 6),
            "abstained": abstained,
            "confidence_flags": ans.confidence_flags,
            "answer_plain_preview": ans.answer_plain[:80] + "..." if len(ans.answer_plain) > 80 else ans.answer_plain
        }
        results.append(res_obj)

        print(f"[{label}] \"{q}\"")
        print(f"   Top-1: {top1_id} ({top1_sc:.6f}) | Top-2: {top2_id} ({top2_sc:.6f}) | Gap: {gap:.6f}")
        print(f"   Abstained: {abstained} | Flags: {ans.confidence_flags}")
        print()

    with open("data/cache/audit8_scores_gaps.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
