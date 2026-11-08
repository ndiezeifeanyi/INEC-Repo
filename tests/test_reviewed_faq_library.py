import json
from pathlib import Path
from src.retrieval.faq_library import FAQLibrary

def test_reviewed_faq_library_structure():
    faq_path = Path("data/processed/reviewed_faq_library.json")
    assert faq_path.exists(), "reviewed_faq_library.json must exist"

    with open(faq_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data["metadata"]
    assert meta["english_review_status"] == "DEVELOPER_DRAFT_PENDING_HUMAN_VERIFICATION"
    assert meta["hausa_review_status"] == "UNREVIEWED_DEVELOPER_DRAFT"
    assert meta["yoruba_review_status"] == "UNREVIEWED_DEVELOPER_DRAFT"
    assert meta["igbo_review_status"] == "UNREVIEWED_DEVELOPER_DRAFT"

    faqs = data["faqs"]
    assert len(faqs) >= 15, f"Expected at least 15 low-risk topic FAQs, found {len(faqs)}"

    for faq in faqs:
        # English assertions
        assert "verbatim_quote" in faq["english"] and len(faq["english"]["verbatim_quote"]) > 10
        assert "short_explanation" in faq["english"] and len(faq["english"]["short_explanation"]) > 10
        assert faq["english"]["review_status"] == "DEVELOPER_DRAFT_PENDING_HUMAN_VERIFICATION"

        # Native draft assertions
        for lang in ["hausa", "yoruba", "igbo"]:
            assert "draft_translation" in faq[lang]
            assert faq[lang]["review_status"] == "UNREVIEWED_DEVELOPER_DRAFT"

        # Exclusion checks: tribunal / offences
        assert "tribunal" not in faq["topic"].lower()
        assert "petition" not in faq["topic"].lower()
        assert "offence" not in faq["topic"].lower()
        assert "penalty" not in faq["topic"].lower()

def test_faq_near_miss_exclusions():
    """Near-miss questions touching offences, penalties, or tribunals must NOT match any FAQ."""
    lib = FAQLibrary()

    near_miss_queries = [
        "Can I vote with someone else's PVC?",
        "Can I vote without my own PVC by using my brother's card?",
        "Can I sell my voter card to a party agent?",
        "What is the penalty if the presiding officer does not sign and stamp the result?",
        "How do I file a petition at the election tribunal to challenge the outcome?",
        "Can a political party agent bribe voters near the polling booth?",
        "What happens if someone steals or snatches the ballot box?",
        "Can I forge an affidavit of nomination papers?",
        "What is the prison fine for voting twice?"
    ]

    for q in near_miss_queries:
        matched = lib.lookup(q, lang="en")
        assert matched is None, f"Query '{q}' should NOT have matched an FAQ, but matched {matched.get('id')}"

def test_faq_valid_civic_matches():
    """Legitimate administrative questions must match their designated low-risk FAQ."""
    lib = FAQLibrary()

    assert lib.lookup("Can I vote without my PVC?", lang="en")["id"] == "FAQ_01_PVC_REQUIREMENT"
    assert lib.lookup("How many days notice must INEC publish before election?", lang="en")["id"] == "FAQ_04_ELECTION_NOTICE_TIMELINE"
    assert lib.lookup("What age can I register to vote?", lang="en")["id"] == "FAQ_05_VOTER_QUALIFICATION_AGE"
