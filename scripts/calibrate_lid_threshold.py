#!/usr/bin/env python3
"""
scripts/calibrate_lid_threshold.py

Calibrates LID confidence threshold empirically across the 30-sample validation split
(tests/data/lid_validation_bench.json), covering en, ha, yo, ig, pcm, and code-switched.
Generates an auditable confusion matrix saved to data/cache/lid_confusion_matrix.json.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.lid.ensemble_lid import EnsembleLID

def run_lid_calibration():
    val_path = Path("tests/data/lid_validation_bench.json")
    with open(val_path, "r", encoding="utf-8") as f:
        val_samples = json.load(f)

    print("=" * 80)
    print("EMPIRICAL LID THRESHOLD CALIBRATION & CONFUSION MATRIX (N=30)")
    print("=" * 80)

    # First pass: collect predictions with raw confidence scores
    engine = EnsembleLID(confidence_threshold=0.0)
    predictions = []

    for item in val_samples:
        sid = item["id"]
        text = item["text"]
        target = item["expected_lang"]
        is_cs = item["is_code_switched"]

        pred_lang, conf, _ = engine.identify(text)
        predictions.append({
            "id": sid,
            "text": text,
            "target": target,
            "pred_lang": pred_lang,
            "confidence": conf,
            "is_code_switched": is_cs
        })
        print(f"[{sid}] Target: {target:<13} | Pred: {pred_lang:<13} | Conf: {conf:.4f} | '{text[:45]}...'")

    # Sweep candidate thresholds
    thresholds = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85]
    print("\n" + "=" * 80)
    print("THRESHOLD SWEEP ON LID VALIDATION SET")
    print(f"{'Threshold':>10} | {'Correct':>8} | {'Disambig (Low-Conf/CS)':>22} | {'False Sure':>10} | {'Effective Acc':>14}")
    print("-" * 80)

    best_thresh = None
    best_eff_acc = -1.0
    sweep_results = []

    for tau in thresholds:
        correct = 0
        disambiguated = 0
        false_sure = 0

        for p in predictions:
            pred = p["pred_lang"]
            target = p["target"]
            conf = p["confidence"]

            if conf < tau or pred == "code_switched":
                disambiguated += 1
                # If target was code-switched or uncertain, disambiguation is the correct safe action
                if target == "code_switched":
                    correct += 1
            else:
                if pred == target:
                    correct += 1
                else:
                    false_sure += 1

        eff_acc = correct / len(predictions)
        sweep_results.append({
            "threshold": tau,
            "correct": correct,
            "disambiguated": disambiguated,
            "false_sure": false_sure,
            "effective_accuracy": eff_acc
        })
        print(f"{tau:>10.2f} | {correct:>8}/{len(predictions)} | {disambiguated:>22} | {false_sure:>10} | {eff_acc:>13.1%}")

        if eff_acc > best_eff_acc:
            best_eff_acc = eff_acc
            best_thresh = tau

    print("=" * 80)
    print(f"Optimal Empirical LID Threshold: tau_LID = {best_thresh:.2f}")
    print(f"Effective Accuracy: {best_eff_acc:.1%}")
    print("=" * 80)

    # Generate Confusion Matrix at optimal threshold
    calibrated_engine = EnsembleLID(confidence_threshold=best_thresh)
    labels = ["en", "ha", "yo", "ig", "pcm", "code_switched"]
    matrix = {t: {p: 0 for p in labels} for t in labels}

    for p in predictions:
        target = p["target"]
        pred_lang, conf, needs_disambig = calibrated_engine.identify(p["text"])
        if needs_disambig and target == "code_switched":
            matrix[target]["code_switched"] += 1
        elif needs_disambig and conf < best_thresh:
            # Marked as needing confirmation
            matrix[target][pred_lang] += 1
        else:
            matrix[target][pred_lang] += 1

    print("\nCONFUSION MATRIX (Row = Ground Truth, Col = Predicted):")
    header = f"{'True / Pred':<15}" + "".join([f"{lbl:>10}" for lbl in labels])
    print(header)
    print("-" * len(header))
    for true_lbl in labels:
        row = f"{true_lbl:<15}" + "".join([f"{matrix[true_lbl][p]:>10}" for p in labels])
        print(row)

    out_file = Path("data/cache/lid_confusion_matrix.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "predictions": predictions,
            "threshold_sweep": sweep_results,
            "optimal_threshold": best_thresh,
            "effective_accuracy": best_eff_acc,
            "confusion_matrix": matrix,
            "labels": labels
        }, f, indent=2)

    print(f"\nSaved confusion matrix to {out_file}")

if __name__ == "__main__":
    run_lid_calibration()

