import json
from pathlib import Path
from src.retrieval.translate_hybrid import TranslationHybridRetriever
from src.generation.prompt_builder import GroundedAnswerGenerator

def test_currency_and_transition():
    base_dir = Path(__file__).resolve().parent.parent
    bench_file = base_dir / "tests" / "data" / "currency_bench.json"

    with open(bench_file, "r", encoding="utf-8") as f:
        bench_data = json.load(f)

    retriever = TranslationHybridRetriever()
    generator = GroundedAnswerGenerator()

    for item in bench_data:
        q = item["query"]
        forbidden = item["forbidden_phrase"]
        expected_doc = item["expected_document"]

        retrieved = retriever.retrieve(q, top_k=3, lang="en")
        answer = generator.generate_answer(q, retrieved, lang="en")

        # 1. Assert forbidden repealed phrases are not present
        assert forbidden.lower() not in answer.answer_text.lower(), (
            f"Failed currency check for query '{q}': found forbidden phrase '{forbidden}' in answer."
        )

        # 2. Assert statutory citations refer to 2026 documents
        assert len(answer.citations) > 0, f"Expected citation for '{q}', but none found."
        top_cite = answer.citations[0]
        all_cited_titles = [c.document_title for c in answer.citations]
        assert "2026" in top_cite.document_title, (
            f"Expected a 2026 statutory document, but got {top_cite.document_title}."
        )

        # 3. For Section 29A, verify UNCONFIRMED status flag
        if "29A" in item["id"] or "29A" in top_cite.section:
            assert top_cite.legal_status == "UNCONFIRMED", (
                f"Section 29A must be flagged UNCONFIRMED, got: {top_cite.legal_status}"
            )
            assert "UNCONFIRMED" in answer.answer_text, (
                "Answer text must explicitly state UNCONFIRMED status."
            )
            assert "Passed by both chambers (Apr/May 2026)" in answer.answer_text, (
                "Answer text must state 'Passed by both chambers (Apr/May 2026)'."
            )
            assert "check the Gazette" in answer.answer_text, (
                "Answer text must advise user to 'check the Gazette'."
            )

    print("All currency tests passed: 2026 statutes enforced, Section 29A classified as UNCONFIRMED.")

if __name__ == "__main__":
    test_currency_and_transition()
