"""
Central Configuration for Electoral Act 2026 & INEC Verification Engine.
Stores statutory facts, unconfirmed legislative amendment notices, and official domain registries.
"""

import os
from typing import Dict, Any

# Section 29A: Unconfirmed Amendment Notice (NOT IN GAZETTE)
# Hard constraint: Never inject unconfirmed amendments into the official gazette corpus.
UNCONFIRMED_AMENDMENTS: Dict[str, Dict[str, Any]] = {
    "29A": {
        "status": "UNCONFIRMED",
        "title": "Electoral Act Amendment (Section 29A - Pre-election Jurisdiction)",
        "chamber_passage": "Passed by both chambers (Apr/May 2026)",
        "assent_status": "Awaiting Gazette / Unconfirmed presidential assent as of 2026-11-07",
        "notice": "Passed by both chambers (Apr/May 2026); I could not confirm presidential assent as of 2026-11-07; check the Gazette.",
        "notice_translations": {
            "en": {
                "text": "Passed by both chambers (Apr/May 2026); I could not confirm presidential assent as of 2026-11-07; check the Gazette.",
                "status": "DRAFT_ENGLISH"
            },
            "ha": {
                "text": "Majalisun biyu sun amince da shi (Afrilu/Mayu 2026); ban sami tabbacin sa hannun shugaban kasa ba har zuwa 2026-11-07; duba Gazette.",
                "status": "UNREVIEWED"
            },
            "yo": {
                "text": "Ile asofin mejeeji fowo si (Osu Igbe/Ebibi 2026); nko le fi idi ifowo si aare mule titi di 2026-11-07; ye Gazette wo.",
                "status": "UNREVIEWED"
            },
            "ig": {
                "text": "Ụlọ omeiwu abụọ kwadoro ya (Eprel/Mee 2026); enweghị m ike nkwenye nbinye aka onye isi ala ruo 2026-11-07; lelee Gazette.",
                "status": "UNREVIEWED"
            }
        },
        "notice_ha": "Majalisun biyu sun amince da shi (Afrilu/Mayu 2026); ban sami tabbacin sa hannun shugaban kasa ba har zuwa 2026-11-07; duba Gazette. [STATUS: UNREVIEWED]",
        "notice_yo": "Ile asofin mejeeji fowo si (Osu Igbe/Ebibi 2026); nko le fi idi ifowo si aare mule titi di 2026-11-07; ye Gazette wo. [STATUS: UNREVIEWED]",
        "notice_ig": "Ụlọ omeiwu abụọ kwadoro ya (Eprel/Mee 2026); enweghị m ike nkwenye nbinye aka onye isi ala ruo 2026-11-07; lelee Gazette. [STATUS: UNREVIEWED]"
    }
}

# Verified Election Dates (treated as given)
ELECTION_TIMETABLE = {
    "presidential_nass": "2027-01-16",
    "governorship_state_assembly": "2027-02-06"
}

# Official Domain Registries
OFFICIAL_INEC_DOMAINS = [
    "inecnigeria.org",
    "cvr.inecnigeria.org",
    "irev.inecnigeria.org"
]

KNOWN_FAKE_DOMAINS = [
    "linksnapro.com",
    "pvc-inecnigeria-org.blogspot.com"
]

# Abstention Safeguards: Recalibrated empirically on frozen validation split (tests/data/score_gap_val_split.json)
# History: In Audit 7, SCORE_GAP_THRESHOLD=0.0001 was inspected-then-set post-hoc.
# Recalibrated across 12 validation queries (unambiguous vs ambiguous ties):
# At tau=0.0010, validation accuracy is 75.0% and F1 is 0.8000 with 100% recall on ambiguous ties.
SCORE_GAP_THRESHOLD = 0.0010
# Electoral Offences section range in Electoral Act 2026 (Part VII: Sections 118 to 133, Gazette Page 54-62)
ELECTORAL_OFFENCES_SECTION_RANGE = (118, 133)

# Language Identification (LID) Configuration (AfroLID + GlotLID Ensemble)
# Empirically calibrated on 30-sample validation split (tests/data/lid_validation_bench.json).
# Sweep across [0.50, 0.85] showed tau=0.85 degraded accuracy to 53.3%; optimal empirical tau=0.75 yields 76.7% effective accuracy.
LID_CONFIDENCE_THRESHOLD = 0.75

# Multilingual Neural Engine Configuration (Phase 1 Deep Dive)
# Behind flags; defaults to False (fallback to TranslationHybridRetriever)
ENABLE_BGE_M3 = os.environ.get("ENABLE_BGE_M3", "false").lower() in ("true", "1", "yes")
ENABLE_BGE_RERANKER = os.environ.get("ENABLE_BGE_RERANKER", "false").lower() in ("true", "1", "yes")
BGE_M3_MODEL_NAME = os.environ.get("BGE_M3_MODEL_NAME", "BAAI/bge-m3")
BGE_RERANKER_MODEL_NAME = os.environ.get("BGE_RERANKER_MODEL_NAME", "BAAI/bge-reranker-v2-m3")

# Multilingual Query Translation Configuration (Phase 3)
# Behind flags; defaults to False (fallback to file cache and offline civic dictionary)
ENABLE_NLLB_LOCAL = os.environ.get("ENABLE_NLLB_LOCAL", "false").lower() in ("true", "1", "yes")
NLLB_MODEL_NAME = os.environ.get("NLLB_MODEL_NAME", "facebook/nllb-200-distilled-600M")
# Nigerian Pidgin strategy: 'rule_mapped' (default, highest MRR 0.700), 'pass_through', or 'abstain'
PIDGIN_HANDLING_STRATEGY = os.environ.get("PIDGIN_HANDLING_STRATEGY", "rule_mapped")

# WhatsApp Cloud API & Webhook Verification (Phase 6)
WHATSAPP_APP_SECRET = os.environ.get("WHATSAPP_APP_SECRET", "")
WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "inec_civic_verify_token_2026")





