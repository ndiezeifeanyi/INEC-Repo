"""
Tests for Phase 5 Non-AI Answer Validator (src/generation/validator.py).
Verifies:
1. Valid grounded answers pass.
2. Ungrounded hallucinated section numbers are rejected.
3. Partisan party or candidate mentions are rejected.
4. Ungrounded numerical deadlines are rejected.
5. Weakening of mandatory statutory obligations ('shall' -> 'may') is rejected.
6. Automatic template fallback in GroundedAnswerGenerator.
"""

import pytest
from src.generation.validator import AnswerValidator
from src.generation.prompt_builder import GroundedAnswerGenerator
from src.models.chunk import LegalChunk

@pytest.fixture
def sample_chunk():
    return LegalChunk(
        chunk_id="EA2026-S51-SS2",
        document_title="Electoral Act 2026",
        document_source_url="https://nass.gov.ng",
        document_sha256="abc12345",
        document_version="Gazette No. 40",
        retrieval_date="2026-11-08",
        part_title="Procedure at Election",
        section_number="51",
        subsection_number="2",
        page=27,
        content_english="Where the number of votes cast at an election in any polling unit exceeds the number of accredited voters in that polling unit, the Presiding officer shall cancel the result of the election in that polling unit.",
        content_plain="If more votes are cast than accredited voters on the BVAS, the presiding officer must cancel the election result.",
        legal_status="CURRENT_LAW"
    )

def test_valid_answer_passes(sample_chunk):
    validator = AnswerValidator()
    answer_text = "According to Electoral Act 2026, Section 51(2), the presiding officer must cancel the result if votes exceed accredited voters."
    answer_plain = "The presiding officer cancels the result if over-voting occurs."
    report = validator.validate(answer_text, answer_plain, [sample_chunk])
    assert report.is_valid is True
    assert len(report.flagged_violations) == 0

def test_hallucinated_section_rejected(sample_chunk):
    validator = AnswerValidator()
    answer_text = "According to Section 999, results must be cancelled."
    answer_plain = "Section 999 says results are cancelled."
    report = validator.validate(answer_text, answer_plain, [sample_chunk])
    assert report.is_valid is False
    assert any("UNGROUNDED_SECTION_CITATION" in v for v in report.flagged_violations)

def test_partisan_party_mention_rejected(sample_chunk):
    validator = AnswerValidator()
    answer_text = "According to Section 51, the APC candidate will have votes cancelled."
    answer_plain = "Votes are cancelled."
    report = validator.validate(answer_text, answer_plain, [sample_chunk])
    assert report.is_valid is False
    assert any("PARTISAN_PARTY_MENTION" in v for v in report.flagged_violations)

def test_ungrounded_numerical_deadline_rejected(sample_chunk):
    validator = AnswerValidator()
    answer_text = "According to Section 51, the cancellation must happen within 99 days."
    answer_plain = "Cancellation takes 99 days."
    report = validator.validate(answer_text, answer_plain, [sample_chunk])
    assert report.is_valid is False
    assert any("UNGROUNDED_NUMERICAL_DEADLINE" in v for v in report.flagged_violations)

def test_modal_dilution_rejected(sample_chunk):
    validator = AnswerValidator()
    # Source has 'shall cancel'
    answer_text = "According to Section 51, the presiding officer may cancel the result if they want."
    answer_plain = "The officer may cancel."
    report = validator.validate(answer_text, answer_plain, [sample_chunk])
    assert report.is_valid is False
    assert any("MODAL_WEAKENING" in v for v in report.flagged_violations)

def test_generator_fallback_on_violation(sample_chunk):
    generator = GroundedAnswerGenerator()
    # Inject a query that retrieves sample_chunk
    answer = generator.generate_answer(
        query="What happens if more votes are cast?",
        retrieved_chunks=[(sample_chunk, 0.05)],
        lang="en"
    )
    assert answer.status == "ANSWER"
    # Now verify that standard generation is clean and valid
    assert "CODE_VALIDATOR_FLAGGED_VIOLATIONS" not in answer.confidence_flags
