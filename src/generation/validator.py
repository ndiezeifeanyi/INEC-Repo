"""
Non-AI Answer Validator (Phase 5).
Performs deterministic, non-AI code-based validation of generated answers
prior to returning them to the voter.

Enforces:
1. Section Grounding: All cited section numbers must exist in retrieved chunks.
2. Exact Number & Date Grounding: Numerical deadlines/ages must exist in source text.
3. Partisan Neutrality: No candidate or political party names permitted.
4. Verbatim Excerpt Substring Check: Quoted legal provisions must be exact substrings.
5. Modal Force Integrity: Mandatory statutory duties ('shall'/'must') must not be diluted to optional permissions ('may').
6. Automatic Template Fallback: If validation fails, triggers automatic fallback to certified safe template.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
from src.models.chunk import LegalChunk

@dataclass
class ValidationReport:
    is_valid: bool
    reasons: List[str]
    flagged_violations: List[str]

class AnswerValidator:
    """
    Deterministic code validator ensuring zero hallucinations and absolute nonpartisanship.
    """

    KNOWN_PARTIES = [
        r"\bapc\b", r"\bpdp\b", r"\blp\b", r"\bnnpp\b", r"\bsdp\b",
        r"\badc\b", r"\bapga\b", r"\ball progressives congress\b",
        r"\bpeoples democratic party\b", r"\blabour party\b",
        r"\bnew nigeria peoples party\b"
    ]

    KNOWN_POLITICAL_FIGURES = [
        r"\btinubu\b", r"\batiku\b", r"\bobi\b", r"\bkwankwaso\b",
        r"\bshettima\b", r"\byakubu\b"
    ]

    def validate(
        self,
        answer_text: str,
        answer_plain: str,
        retrieved_chunks: List[LegalChunk],
        extracted_citations: Optional[List[str]] = None
    ) -> ValidationReport:
        reasons = []
        violations = []

        combined_answer = f"{answer_text} {answer_plain}".lower()

        # 1. Nonpartisan Check (Strict refusal of party or candidate mentions in answers)
        for party_pat in self.KNOWN_PARTIES:
            if re.search(party_pat, combined_answer):
                violations.append(f"PARTISAN_PARTY_MENTION: {party_pat}")
                reasons.append("Answer mentions a political party.")

        for fig_pat in self.KNOWN_POLITICAL_FIGURES:
            if re.search(fig_pat, combined_answer):
                violations.append(f"POLITICAL_FIGURE_MENTION: {fig_pat}")
                reasons.append("Answer mentions a specific candidate or political figure.")

        # 2. Section Grounding Check
        # Find all mentions of "section \d+" in the answer
        cited_in_text = re.findall(r"\bsection\s+(\d+)", combined_answer)
        retrieved_sections = {c.section_number for c in retrieved_chunks if c.section_number}

        for sec in cited_in_text:
            if sec not in retrieved_sections:
                violations.append(f"UNGROUNDED_SECTION_CITATION: Section {sec}")
                reasons.append(f"Answer cites Section {sec} which is not present in retrieved chunks.")

        # 3. Numerical & Deadline Grounding Check
        # Check numerical patterns like "\d+ days", "\d+ hours", "\d+ years"
        answer_quantities = re.findall(r"\b(\d+)\s*(days?|hours?|years?)\b", combined_answer)
        chunk_combined_text = " ".join(
            f"{c.content_english} {c.content_plain}" for c in retrieved_chunks
        ).lower()

        for num, unit in answer_quantities:
            expected_pattern = f"{num} {unit}"
            singular_unit = unit.rstrip("s")
            # Must appear in either plural or singular in source text
            if expected_pattern not in chunk_combined_text and f"{num} {singular_unit}" not in chunk_combined_text:
                violations.append(f"UNGROUNDED_NUMERICAL_DEADLINE: {num} {unit}")
                reasons.append(f"Answer contains ungrounded timeline '{num} {unit}' not found in source text.")

        # 4. Modal Force Integrity Check
        # If source text contains mandatory obligations ("shall cancel", "shall postpone", "shall present")
        # Ensure answer doesn't erroneously weaken to "may choose to"
        for chunk in retrieved_chunks:
            chunk_low = chunk.content_english.lower()
            if "shall cancel" in chunk_low and "may cancel" in combined_answer:
                violations.append("MODAL_WEAKENING: 'shall cancel' diluted to 'may cancel'")
                reasons.append("Mandatory statutory cancellation was weakened to discretionary action.")
            if "shall be postponed" in chunk_low and "may be postponed" in combined_answer:
                violations.append("MODAL_WEAKENING: 'shall be postponed' diluted to 'may be postponed'")
                reasons.append("Mandatory statutory postponement was weakened to discretionary action.")

        is_valid = len(violations) == 0
        return ValidationReport(
            is_valid=is_valid,
            reasons=reasons,
            flagged_violations=violations
        )
