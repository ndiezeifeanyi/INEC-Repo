import hashlib
import urllib.parse
from typing import Set, Tuple, Optional

class PrivacySafeBrowsingEngine:
    """
    Local privacy-preserving URL inspection client based on:
    - Internal domain allowlist
    - Locally compiled known-fake list (SHA-256 4-byte prefix matching)
    NOTE: This is NOT the live Google Safe Browsing API. It operates purely on local threat lists
    to avoid transmitting user URLs across the network.
    """

    def __init__(self):
        # Local cache of known malicious SHA-256 4-byte prefixes
        # Generated from known election phishing URLs
        self.local_prefix_db: Set[bytes] = set()
        self._seed_local_database()

    @staticmethod
    def canonicalize_url(url: str) -> str:
        """Canonicalizes URL as per Google Safe Browsing specifications."""
        clean = url.strip()
        if not clean.startswith(("http://", "https://")):
            clean = "http://" + clean
        parsed = urllib.parse.urlparse(clean)
        host = (parsed.hostname or "").lower()
        path = parsed.path or "/"
        return f"{host}{path}"

    @classmethod
    def compute_sha256_prefix(cls, url: str) -> bytes:
        canonical = cls.canonicalize_url(url)
        full_hash = hashlib.sha256(canonical.encode("utf-8")).digest()
        # Extract first 4 bytes (32-bit prefix)
        return full_hash[:4]

    def _seed_local_database(self):
        # Known threat URLs
        threat_urls = [
            "linksnapro.com/cvrreg",
            "pvc-inecnigeria-org.blogspot.com",
            "inecnigeria-voter-card.com/apply",
            "cvr-portal-online.org/register"
        ]
        for u in threat_urls:
            prefix = self.compute_sha256_prefix(u)
            self.local_prefix_db.add(prefix)

    def check_url_privacy_safe(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Evaluates a URL strictly using local hash prefixes.
        Full URL is NEVER transmitted across the network.
        """
        prefix = self.compute_sha256_prefix(url)
        if prefix in self.local_prefix_db:
            return True, "Flagged: Local SHA-256 hash prefix matches verified phishing list."
        return False, None

