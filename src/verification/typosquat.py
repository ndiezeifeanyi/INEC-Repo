import unicodedata
from typing import Tuple, Optional
from src.verification.allowlist import DomainAllowlistVerifier

class TyposquatDetector:
    """
    Detects typosquatting, IDN homoglyphs, and known fake domains mimicking INEC.
    """

    KNOWN_FRAUD_DOMAINS = {
        "linksnapro.com",
        "pvc-inecnigeria-org.blogspot.com",
        "inecnigeria-voter-card.com",
        "cvr-portal-online.org",
        "inecnigeria-grant.org"
    }

    CONFUSABLES = {
        '1': 'i',
        '0': 'o',
        '3': 'e',
        '@': 'a',
        'vv': 'w'
    }

    @staticmethod
    def _levenshtein(s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return TyposquatDetector._levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)

        prev = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            curr = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev[j + 1] + 1
                deletions = curr[j] + 1
                substitutions = prev[j] + (c1 != c2)
                curr.append(min(insertions, deletions, substitutions))
            prev = curr
        return prev[-1]

    @classmethod
    def check_suspicious(cls, url_or_host: str) -> Tuple[bool, Optional[str]]:
        hostname = DomainAllowlistVerifier.clean_hostname(url_or_host)
        if not hostname:
            return False, None

        # Check known fakes list
        for fake in cls.KNOWN_FRAUD_DOMAINS:
            if fake in hostname:
                return True, f"High Risk: Matches known fraudulent domain list ({fake})"

        # Check if contains official keywords embedded inside suspicious TLDs
        if "cvr" in hostname and "inecnigeria" in hostname and not hostname.endswith("inecnigeria.org"):
            return True, f"High Risk: Counterfeit CVR domain structure ({hostname})"

        # Normalize homoglyphs and leetspeak
        normalized = hostname
        for char, target in cls.CONFUSABLES.items():
            normalized = normalized.replace(char, target)

        # Remove punycode/unicode accents
        normalized = unicodedata.normalize('NFKD', normalized).encode('ASCII', 'ignore').decode('utf-8')

        # Check distance to base domain
        base_target = "inecnigeria"
        domain_parts = normalized.split('.')
        for part in domain_parts:
            # Skip if exact official target
            if part == base_target:
                continue
            dist = cls._levenshtein(part, base_target)
            if 1 <= dist <= 2:
                return True, f"High Risk: Typosquatted mimic of '{base_target}' detected ('{part}')"

        return False, None
