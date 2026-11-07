import re

class PlainLanguageConverter:
    """Simplifies complex legal statutes into accessible Grade-6 reading levels."""

    LEGAL_JARGON_MAP = {
        r"\bnotwithstanding the provisions of\b": "even if another rule says",
        r"\bpursuant to\b": "under",
        r"\bshall be deemed to be\b": "is considered",
        r"\baforementioned\b": "earlier mentioned",
        r"\bforthwith\b": "immediately",
        r"\bcommence\b": "start",
        r"\bprescribed manner\b": "official procedure",
        r"\bintending voter\b": "voter",
        r"\bstand adjourned\b": "is postponed",
        r"\bvoid\b": "cancelled and invalid"
    }

    @classmethod
    def to_plain_english(cls, legal_text: str) -> str:
        plain = legal_text
        for pattern, replacement in cls.LEGAL_JARGON_MAP.items():
            plain = re.sub(pattern, replacement, plain, flags=re.IGNORECASE)
        return plain
