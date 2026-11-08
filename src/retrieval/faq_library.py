"""
src/retrieval/faq_library.py

Reviewed FAQ Library Service (Phase 4).
Loads pre-reviewed civic QA pairs covering 16 low-risk electoral topics.
Strictly excludes tribunals, offences, and partisan questions.

Guarantees:
- English answers are labeled DEVELOPER_DRAFT_PENDING_HUMAN_VERIFICATION.
- Indigenous languages are UNREVIEWED_DEVELOPER_DRAFT with dual English quote.
- Strict negative exclusions prevent near-miss offences/tribunal queries from matching.
"""

import re
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

class FAQLibrary:
    """
    Fast-path lookup service for 16 pre-reviewed civic administrative topics.
    Enforces negative exclusion patterns so that questions involving electoral offences,
    penalties, vote-buying, impersonation, or election petitions never match an FAQ.
    """

    # Negative exclusion patterns: Any query touching offences, penalties, petitions,
    # or illegal acts must NOT match an FAQ and must fall through to retrieval/safeguards.
    EXCLUSION_PATTERNS = [
        r"\btribunal\b",
        r"\bpetition\b",
        r"\bchallenge\s+(the\s+)?(result|outcome|election)\b",
        r"\bbribe\b",
        r"\bbribing\b",
        r"\bbribery\b",
        r"\bsell\b",
        r"\bselling\b",
        r"\bbuy\b",
        r"\bbuying\b",
        r"\bpenalty\b",
        r"\bpenalties\b",
        r"\bprison\b",
        r"\bfine\b",
        r"\barrest\b",
        r"\bforge\b",
        r"\bforged\b",
        r"\bforgery\b",
        r"\bsteal\b",
        r"\bstolen\b",
        r"\bsnatch\b",
        r"\bsnatching\b",
        r"\bsomeone\s+else\b",
        r"\banother\s+person\b",
        r"\bimpersonat(e|ing|ion)\b",
        r"\bbrother\b",
        r"\bsister\b",
        r"\bfather\b",
        r"\bmother\b",
        r"\bfriend\b"
    ]

    def __init__(self, library_path: Optional[Path] = None):
        if library_path is None:
            self.library_path = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "reviewed_faq_library.json"
        else:
            self.library_path = library_path

        self.metadata = {}
        self.faqs: List[Dict[str, Any]] = []
        self._compiled_exclusions = [re.compile(p, re.IGNORECASE) for p in self.EXCLUSION_PATTERNS]
        self._load()

    def _load(self):
        if self.library_path.exists():
            with open(self.library_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.metadata = data.get("metadata", {})
                self.faqs = data.get("faqs", [])

    def lookup(self, query: str, lang: str = "en") -> Optional[Dict[str, Any]]:
        """
        Looks up a voter query against pre-reviewed low-risk civic topics.
        Returns None if:
        1. Query triggers any negative exclusion pattern (offences, penalties, petitions, impersonation).
        2. Query does not contain all required signature keywords for an FAQ topic.
        """
        lowered = query.lower()

        # Step 1: Check negative exclusion filters
        for pattern in self._compiled_exclusions:
            if pattern.search(lowered):
                return None

        # Step 2: Signature token sets for the 16 pre-reviewed low-risk topics
        signatures = [
            ("FAQ_01_PVC_REQUIREMENT", ["vote", "pvc", "without"], ["kaadi", "pvc"], ["katin", "pvc"], ["kaadi", "pvc"]),
            ("FAQ_02_BVAS_FAILURE_BACKUP", ["bvas", "fail"], ["ero", "bvas"], ["na'urar", "bvas", "lalace"], ["igwe", "bvas"]),
            ("FAQ_03_OVERVOTING_CANCELLATION", ["over-voting", "exceed"], ["tantance", "po ju"], ["yawan kuri'u", "zarce"], ["karie"]),
            ("FAQ_04_ELECTION_NOTICE_TIMELINE", ["notice", "days", "publish"], ["ifitonile", "ojo"], ["sanarwar", "kwanaki"], ["ozi", "ubochi"]),
            ("FAQ_05_VOTER_QUALIFICATION_AGE", ["age", "register"], ["ojo ori"], ["shekaru"], ["afo"]),
            ("FAQ_06_VOTER_TRANSFER_RESIDENCE", ["transfer", "residence"], ["ibugbe", "pada"], ["canza", "wurin zama"], ["kwagara"]),
            ("FAQ_07_DELIVERY_NOMINATION_PAPERS", ["nomination", "deliver"], ["yiyan", "oludije"], ["takardun", "tsayawa takara"], ["akwukwo", "okwa"]),
            ("FAQ_08_POLLING_UNIT_RESULT_DISPLAY", ["sign", "stamp", "result"], ["buwolu", "abajade"], ["sa hannu", "tambari", "sakamako"], ["banye aka", "mpụta"]),
            ("FAQ_09_ELECTRONIC_TRANSMISSION", ["transmit", "irev"], ["gbe", "irev"], ["tura", "irev"], ["ziga", "irev"]),
            ("FAQ_10_COLLATION_VERIFICATION", ["verify", "collation"], ["ayewo", "igba wole"], ["tabbatar", "tattara"], ["achikota"]),
            ("FAQ_11_VOTER_REGISTER_INSPECTION", ["display", "voter register", "inspection"], ["ayewo", "iforukosile", "meje"], ["rajistar", "kwanaki bakwai"], ["ileba anya", "ubochi asaa"]),
            ("FAQ_12_CORRECTION_OF_VOTER_REGISTER", ["claims", "objections", "revision officer"], ["osise atunse", "ejo"], ["jami'an bitar", "korafe-korafe"], ["dozie mkpesa"]),
            ("FAQ_13_HOURS_OF_POLL", ["opening of poll", "ballot box empty"], ["apoti ibo", "titi pa"], ["bude rumfar", "akwatin zabe"], ["emeghe igbe vootu"]),
            ("FAQ_14_ASSISTANCE_TO_DISABLED_VOTERS", ["disability", "visually impaired", "assist"], ["ailera oju", "ran lowo"], ["makaho", "taimaka"], ["nkwaru anya", "nyere aka"]),
            ("FAQ_15_ACCREDITED_POLLING_AGENTS", ["polling agent", "political party agent", "14 days"], ["asoju ibudo", "14"], ["wakilin rumfar", "14"], ["onye nnochi anya", "14"]),
            ("FAQ_16_SECRET_BALLOT_IDENTIFICATION", ["secret ballot", "mark", "identified", "reject"], ["idibo asiri", "iwe ibo"], ["zabe na sirri", "shaidar yatsa"], ["vootu bu ihe nzuzo"])
        ]

        matched_faq_id = None
        for faq_id, en_keys, yo_keys, ha_keys, ig_keys in signatures:
            keys = en_keys if lang in ("en", "pcm") else (yo_keys if lang == "yo" else (ha_keys if lang == "ha" else ig_keys))
            if all(k in lowered for k in keys):
                matched_faq_id = faq_id
                break

        if not matched_faq_id:
            return None

        for faq in self.faqs:
            if faq["id"] == matched_faq_id:
                return faq

        return None
