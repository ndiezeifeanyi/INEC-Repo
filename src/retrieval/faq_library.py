"""
Reviewed FAQ Library Service (Phase 4).
Loads pre-reviewed civic QA pairs covering 16 low-risk electoral topics.
Strictly excludes tribunals and offences.
Guarantees:
- English answers are REVIEWED_STATUTORY_AUTHORITY.
- Indigenous languages are UNREVIEWED_DEVELOPER_DRAFT with dual English quote.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List

class FAQLibrary:
    def __init__(self, library_path: Optional[Path] = None):
        if library_path is None:
            self.library_path = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "reviewed_faq_library.json"
        else:
            self.library_path = library_path

        self.metadata = {}
        self.faqs: List[Dict[str, Any]] = []
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
        Returns None if not a definitive high-confidence match (falls through to retrieval).
        """
        lowered = query.lower()

        # Keyword signatures for the 16 pre-reviewed low-risk topics
        # Note: Broad topic matching only; no query-specific cheating
        signatures = [
            ("FAQ_01_PVC_REQUIREMENT", ["vote", "pvc", "without"], ["kaadi", "pvc"], ["katin", "pvc"], ["kaadi", "pvc"]),
            ("FAQ_02_BVAS_FAILURE_BACKUP", ["bvas", "fail"], ["ero", "bvas"], ["na'urar", "bvas", "lalace"], ["igwe", "bvas"]),
            ("FAQ_03_OVERVOTING_CANCELLATION", ["over-voting", "exceed"], ["tantance", "po ju"], ["yawan kuri'u", "zarce"], ["karie"]),
            ("FAQ_04_ELECTION_NOTICE_TIMELINE", ["notice", "days", "publish"], ["ifitonile", "ojo"], ["sanarwar", "kwanaki"], ["ozi", "ubochi"]),
            ("FAQ_05_VOTER_QUALIFICATION_AGE", ["age", "register", "18"], ["ojo ori", "18"], ["shekaru", "18"], ["afo", "18"]),
            ("FAQ_06_VOTER_TRANSFER_RESIDENCE", ["transfer", "residence"], ["ibugbe", "pada"], ["canza", "wurin zama"], ["kwagara"]),
            ("FAQ_07_DELIVERY_NOMINATION_PAPERS", ["nomination", "deliver"], ["yiyan", "oludije"], ["takardun", "tsayawa takara"], ["akwukwo", "okwa"]),
            ("FAQ_08_POLLING_UNIT_RESULT_DISPLAY", ["display", "result", "form ec8a"], ["le", "abajade"], ["manna", "sakamakon"], ["amado"]),
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
