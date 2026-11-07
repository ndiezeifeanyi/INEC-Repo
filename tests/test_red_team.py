import json
from pathlib import Path
from src.generation.prompt_builder import GroundedAnswerGenerator

def test_red_team_and_refusals():
    base_dir = Path(__file__).resolve().parent.parent
    bench_file = base_dir / "tests" / "data" / "refusal_bench.json"

    with open(bench_file, "r", encoding="utf-8") as f:
        bench_data = json.load(f)

    generator = GroundedAnswerGenerator()

    for item in bench_data:
        q = item["query"]
        lang = item.get("language", "en")
        req_sub = item["required_refusal_substring"].lower()

        answer = generator.generate_answer(q, [], lang=lang)

        # 1. Assert confidence flag indicates refusal safeguard
        assert "REFUSAL_SAFEGUARD_TRIGGERED" in answer.confidence_flags, (
            f"Expected REFUSAL_SAFEGUARD_TRIGGERED for query: '{q}'"
        )

        # 2. Assert no citations are attached to refusals
        assert len(answer.citations) == 0, (
            f"Refusal response should not attach legal citations for query: '{q}'"
        )

        # 3. Assert refusal message contains expected language-specific refusal text
        ans_lower = answer.answer_text.lower()
        assert req_sub in ans_lower, (
            f"Refusal answer for '{q}' did not contain required phrase '{req_sub}'. Got: '{answer.answer_text}'"
        )

    print("All red-team adversarial refusal tests passed.")

if __name__ == "__main__":
    test_red_team_and_refusals()
