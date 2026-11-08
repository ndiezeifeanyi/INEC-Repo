import json
from pathlib import Path
from src.config import SCORE_GAP_THRESHOLD

def test_score_gap_threshold_calibrated():
    """Verify SCORE_GAP_THRESHOLD is 0.0010 as calibrated on frozen validation split."""
    assert SCORE_GAP_THRESHOLD == 0.0010

def test_score_gap_calibration_artifacts_exist():
    """Verify the validation split and calibration output files exist."""
    val_split = Path("tests/data/score_gap_val_split.json")
    calib_cache = Path("data/cache/score_gap_calibration.json")
    assert val_split.exists()
    assert calib_cache.exists()

    with open(calib_cache, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["optimal_threshold"] == 0.0010
    assert data["optimal_accuracy"] >= 0.70
