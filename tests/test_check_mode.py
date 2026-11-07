import json
from pathlib import Path
from src.verification.matcher import OfficialSourceChecker

def test_check_mode_accuracy():
    base_dir = Path(__file__).resolve().parent.parent
    bench_file = base_dir / "tests" / "data" / "check_bench.json"

    with open(bench_file, "r", encoding="utf-8") as f:
        bench_data = json.load(f)

    checker = OfficialSourceChecker()

    for item in bench_data:
        inp = item["input"]
        expected = item["expected_status"]

        result = checker.verify(inp)

        # 1. Status match
        assert result.status == expected, (
            f"Failed check for '{inp}'. Expected status '{expected}', got '{result.status}'."
        )

        # 2. Mandatory disclaimer verification
        assert "This check compares inputs" in result.disclaimer, (
            "Mandatory disclaimer missing from verification output."
        )

        # 3. cvr.inecnigeria.org CNAME false-positive safeguard
        if "cvr.inecnigeria.org" in inp:
            assert result.status == "Matches an official source", (
                "CRITICAL REGRESSION: cvr.inecnigeria.org was falsely rejected due to CNAME routing!"
            )

    print("All Check Mode verification tests passed.")

if __name__ == "__main__":
    test_check_mode_accuracy()
