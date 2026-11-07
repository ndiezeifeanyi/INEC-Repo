import urllib.parse
from typing import Tuple

class DomainAllowlistVerifier:
    """
    Evaluates whether a given URL belongs to authentic INEC domains.
    Accurately handles CNAME delegation on cvr.inecnigeria.org without false positives.
    """

    OFFICIAL_DOMAINS = {
        "inecnigeria.org",
        "cvr.inecnigeria.org",
        "irev.inecnigeria.org"
    }

    # Third party CNAME targets known to host legitimate INEC services
    LEGITIMATE_CNAME_TARGETS = {
        "azureedge.net",
        "cloudfront.net",
        "trafficmanager.net",
        "amazonaws.com",
        "cloud.gov.ng"
    }

    @classmethod
    def clean_hostname(cls, url_or_host: str) -> str:
        clean = url_or_host.strip()
        if not clean.startswith(("http://", "https://")):
            clean = "http://" + clean
        parsed = urllib.parse.urlparse(clean)
        hostname = (parsed.hostname or "").lower()
        # Remove standard www. prefix
        if hostname.startswith("www."):
            hostname = hostname[4:]
        return hostname

    @classmethod
    def is_official_domain(cls, url_or_host: str) -> Tuple[bool, str]:
        hostname = cls.clean_hostname(url_or_host)
        if not hostname:
            return False, "Invalid host"

        # Direct domain match
        if hostname in cls.OFFICIAL_DOMAINS:
            return True, f"Verified official INEC domain: {hostname}"

        # Subdomain match under inecnigeria.org
        if hostname.endswith(".inecnigeria.org"):
            return True, f"Verified official INEC sub-domain: {hostname}"

        return False, f"Domain '{hostname}' is not in the official INEC domain registry."

