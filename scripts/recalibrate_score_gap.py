#!/usr/bin/env python3
"""
scripts/recalibrate_score_gap.py

Empirically recalibrate SCORE_GAP_THRESHOLD using a frozen validation split
(tests/data/score_gap_val_split.json). This replaces the post-hoc 0.0001 setting
with an objective, data-driven threshold derived prior to test-split evaluation.
"""

import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.retrieval.translate_hybrid import TranslationHybridRetriever

def recalibrate():
    val_path = Path("tests/data/score_gap_val_split.json")
    with open(val_path, "r", encoding="utf-8") as f:
        val_data = json.load(f)

    retriever = TranslationHybridRetriever(cache_enabled=True)
    results = []

    print("=" * 80)
    print("EMPIRICAL SCORE GAP CALIBRATION (FROZEN VALIDATION SPLIT, N=12)")
    print("=" * 80)

    for item in val_data:
        qid = item["id"]
        q = item["query"]
        should_abstain = item["should_abstain"]
        cat = item["category"]

        chunks = retriever.retrieve(q, top_k=3)
        if len(chunks) < 2:
            gap = 1.0
            top1_id = chunks[0][0].chunk_id if chunks else "NONE"
            top2_id = "NONE"
            s1 = chunks[0][1] if chunks else 0.0
            s2 = 0.0
        else:
            s1 = chunks[0][1]
            s2 = chunks[1][1]
            gap = round(s1 - s2, 7)
            top1_id = chunks[0][0].chunk_id
            top2_id = chunks[1][0].chunk_id

        results.append({
            "id": qid,
            "query": q,
            "category": cat,
            "should_abstain": should_abstain,
            "top1_id": top1_id,
            "top2_id": top2_id,
            "top1_score": s1,
            "top2_score": s2,
            "gap": gap
        })

        print(f"[{qid}] '{q[:45]}...'")
        print(f"       Category: {cat} | Target Abstain: {should_abstain}")
        print(f"       Top-1: {top1_id} ({s1:.6f}) | Top-2: {top2_id} ({s2:.6f}) | Gap: {gap:.6f}")

    # Sweep thresholds to find optimal threshold separating should_abstain=True vs False
    candidate_thresholds = [
        0.00005, 0.0001, 0.0002, 0.0003, 0.0005, 0.0008, 0.0010, 0.0012, 0.0015, 0.0020, 0.0030, 0.0050
    ]

    print("\n" + "=" * 80)
    print("THRESHOLD SWEEP ON VALIDATION SET")
    print(f"{'Threshold':>12} | {'TP':>4} | {'FP':>4} | {'TN':>4} | {'FN':>4} | {'Accuracy':>10} | {'F1-Score':>10}")
    print("-" * 80)

    best_thresh = None
    best_acc = -1.0
    best_f1 = -1.0

    sweep_records = []
    for tau in candidate_thresholds:
        tp = fp = tn = fn = 0
        for r in results:
            pred_abstain = (r["gap"] <= tau)
            target = r["should_abstain"]
            if pred_abstain and target:
                tp += 1
            elif pred_abstain and not target:
                fp += 1
            elif not pred_abstain and not target:
                tn += 1
            else:
                fn += 1

        acc = (tp + tn) / len(results)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        sweep_records.append({
            "threshold": tau,
            "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "accuracy": acc, "f1": f1
        })
        print(f"{tau:>12.6f} | {tp:>4} | {fp:>4} | {tn:>4} | {fn:>4} | {acc:>9.1%} | {f1:>10.4f}")

        if acc > best_acc or (acc == best_acc and f1 > best_f1):
            best_acc = acc
            best_f1 = f1
            best_thresh = tau

    print("=" * 80)
    print(f"Optimal Recalibrated Threshold: SCORE_GAP_THRESHOLD = {best_thresh:.6f}")
    print(f"Validation Accuracy: {best_acc:.1%} | Validation F1: {best_f1:.4f}")
    print("=" * 80)

    out_file = Path("data/cache/score_gap_calibration.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "validation_results": results,
            "threshold_sweep": sweep_records,
            "optimal_threshold": best_thresh,
            "optimal_accuracy": best_acc,
            "optimal_f1": best_f1
        }, f, indent=2)

    return best_thresh

if __name__ == "__main__":
    recalibrate()
