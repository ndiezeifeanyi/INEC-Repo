import json
from pathlib import Path

def test_reviewed_faq_library_structure():
    faq_path = Path("data/processed/reviewed_faq_library.json")
    assert faq_path.exists(), "reviewed_faq_library.json must exist"

    with open(faq_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data["metadata"]
    assert meta["english_review_status"] == "REVIEWED_STATUTORY_AUTHORITY"
    assert meta["hausa_review_status"] == "UNREVIEWED_DEVELOPER_DRAFT"
    assert meta["yoruba_review_status"] == "UNREVIEWED_DEVELOPER_DRAFT"
    assert meta["igbo_review_status"] == "UNREVIEWED_DEVELOPER_DRAFT"

    faqs = data["faqs"]
    assert len(faqs) >= 15, f"Expected at least 15 low-risk topic FAQs, found {len(faqs)}"

    for faq in faqs:
        # English assertions
        assert "verbatim_quote" in faq["english"] and len(faq["english"]["verbatim_quote"]) > 10
        assert "short_explanation" in faq["english"] and len(faq["english"]["short_explanation"]) > 10
        assert faq["english"]["review_status"] == "REVIEWED_STATUTORY_AUTHORITY"

        # Native draft assertions
        for lang in ["hausa", "yoruba", "igbo"]:
            assert "draft_translation" in faq[lang]
            assert faq[lang]["review_status"] == "UNREVIEWED_DEVELOPER_DRAFT"

        # Exclusion checks: tribunal / offences
        assert "tribunal" not in faq["topic"].lower()
        assert "petition" not in faq["topic"].lower()
        assert "offence" not in faq["topic"].lower()
        assert "penalty" not in faq["topic"].lower()

