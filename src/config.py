"""
Central Configuration for Electoral Act 2026 & INEC Verification Engine.
Stores statutory facts, unconfirmed legislative amendment notices, and official domain registries.
"""

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

# Abstention Safeguards (Audit 7 Pre-registered Thresholds)
# Score-gap threshold: If (top_1_score - top_2_score) <= SCORE_GAP_THRESHOLD, top-1 is not clearly ahead.
SCORE_GAP_THRESHOLD = 0.0001
# Electoral Offences section range in Electoral Act 2026 (Part VII: Sections 114 to 135)
ELECTORAL_OFFENCES_SECTION_RANGE = (114, 135)


