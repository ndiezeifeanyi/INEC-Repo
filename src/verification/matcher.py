import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from src.models.chunk import VerificationResult
from src.verification.allowlist import DomainAllowlistVerifier
from src.verification.typosquat import TyposquatDetector
from src.verification.safe_browsing import PrivacySafeBrowsingEngine

class OfficialSourceChecker:
    """
    Independent verification engine for links and messages.
    Strictly outputs one of three permitted states:
      1. 'Matches an official source'
      2. 'Does not match any official source I can check'
      3. 'Can't tell'
    Never judges political statements as True or False.
    """

    def __init__(self, bulletins_path: Optional[Path] = None):
        self.bulletins: List[Dict[str, str]] = []
        self.safe_browsing = PrivacySafeBrowsingEngine()
        self._load_bulletins(bulletins_path)

    def _load_bulletins(self, bulletins_path: Optional[Path] = None):
        if bulletins_path is None:
            bulletins_path = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "inec_bulletins.jsonl"
        if bulletins_path.exists():
            with open(bulletins_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        self.bulletins.append(json.loads(line))

    @staticmethod
    def is_url(text: str) -> bool:
        clean = text.strip()
        return bool(re.match(r"^(https?://)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$", clean))

    def _normalize_text(self, text: str) -> str:
        clean = "".join(c.lower() if c.isalnum() or c.isspace() else " " for c in text)
        return " ".join(clean.split())

    def verify(self, input_text: str) -> VerificationResult:
        input_clean = input_text.strip()

        # Case A: URL / Link check
        if self.is_url(input_clean):
            # 1. Exact allowlist check
            is_official, note = DomainAllowlistVerifier.is_official_domain(input_clean)
            if is_official:
                return VerificationResult(
                    input_item=input_clean,
                    type="url",
                    status="Matches an official source",
                    matched_source=DomainAllowlistVerifier.clean_hostname(input_clean),
                    confidence_notes=f"Confirmed authentic INEC domain: {note}",
                    corpus_size=len(self.bulletins),
                    corpus_last_updated="2026-11-07"
                )

            # 2. Typosquat / known counterfeit detection
            is_typo, typo_note = TyposquatDetector.check_suspicious(input_clean)
            if is_typo:
                return VerificationResult(
                    input_item=input_clean,
                    type="url",
                    status="Does not match any official source I can check",
                    matched_source=None,
                    confidence_notes=f"Deceptive site warning: {typo_note}",
                    corpus_size=len(self.bulletins),
                    corpus_last_updated="2026-11-07"
                )

            # 3. Local known-fake hash prefix check
            is_malicious, sb_note = self.safe_browsing.check_url_privacy_safe(input_clean)
            if is_malicious:
                return VerificationResult(
                    input_item=input_clean,
                    type="url",
                    status="Does not match any official source I can check",
                    matched_source=None,
                    confidence_notes=f"Threat intelligence alert: {sb_note}",
                    corpus_size=len(self.bulletins),
                    corpus_last_updated="2026-11-07"
                )

            # 4. Unknown domain -> Default to "Does not match any official source I can check" with explicit corpus limits
            return VerificationResult(
                input_item=input_clean,
                type="url",
                status="Does not match any official source I can check",
                matched_source=None,
                confidence_notes="Domain is not registered in official INEC domain records.",
                corpus_size=len(self.bulletins),
                corpus_last_updated="2026-11-07"
            )

        # Case B: Message / Claim check against published official bulletins
        norm_input = self._normalize_text(input_clean)
        input_words = set(norm_input.split())

        best_match = None
        best_overlap = 0.0

        for b in self.bulletins:
            norm_b = self._normalize_text(b["text"])
            b_words = set(norm_b.split())
            if not b_words:
                continue

            # Check exact substring match
            if norm_input in norm_b or norm_b in norm_input:
                best_match = b
                best_overlap = 1.0
                break

            # Check Jaccard word overlap
            overlap = len(input_words.intersection(b_words)) / len(input_words.union(b_words))
            if overlap > best_overlap:
                best_overlap = overlap
                best_match = b

        if best_overlap >= 0.40 and best_match:
            return VerificationResult(
                input_item=input_clean,
                type="message",
                status="Matches an official source",
                matched_source=f"{best_match['title']} ({best_match['source_url']})",
                confidence_notes=f"Matches verified INEC release published on {best_match['date']}.",
                corpus_size=len(self.bulletins),
                corpus_last_updated="2026-11-07"
            )

        # In all other cases, strictly DEFAULT to "Can't tell"
        return VerificationResult(
            input_item=input_clean,
            type="message",
            status="Can't tell",
            matched_source=None,
            confidence_notes="Does not match any published bulletin in the local indexed corpus. Defaulting to 'Can't tell' as check is not exhaustive.",
            corpus_size=len(self.bulletins),
            corpus_last_updated="2026-11-07"
        )

