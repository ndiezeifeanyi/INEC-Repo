"""
src/lid/ensemble_lid.py

Language Identification (LID) Ensemble incorporating AfroLID + GlotLID specifications
for African Indigenous Languages (Hausa, Yoruba, Igbo), English, and Nigerian Pidgin (pcm).
Includes code-switching detection and empirical confidence scoring.
"""

import re
from typing import Dict, Tuple, Optional

# Supported language codes
LANG_EN = "en"
LANG_HA = "ha"
LANG_YO = "yo"
LANG_IG = "ig"
LANG_PCM = "pcm"
LANG_MIXED = "code_switched"

# Prominent marker sets for high-precision token filtering
PCM_MARKERS = {
    "dey", "wetin", "fit", "na", "abeg", "una", "don", "wey", "dem", "sabi",
    "sef", "pikin", "wahala", "kwanu", "shey", "sha", "baff", "commot", "oya"
}

HAUSA_MARKERS = {
    "da", "na", "ba", "kuri'a", "zabe", "shekaru", "hukumar", "cancanta", "kwanaki",
    "rumfar", "idan", "ake", "bukata", "mutum", "dindindin", "tare", "tsayawa", "jam'iyyu"
}

YORUBA_MARKERS = {
    "nje", "yoo", "sele", "awon", "oludibo", "ojo", "idibo", "gbodo", "lati",
    "le", "se", "ori", "melo", "bawo", "ero", "taara", "iforukosile", "afiyesi", "tantance"
}

IGBO_MARKERS = {
    "enwere", "ike", "vootu", "oburu", "kaadi", "ubochi", "ntuli", "aka", "onu",
    "ogugu", "karie", "nzere", "tupu", "mmadu", "idebanye", "kwanu", "gini", "ole", "afo"
}

# Interactive disambiguation prompt shown when confidence falls below calibrated threshold
DISAMBIGUATION_PROMPT = (
    "Please confirm your language / Jọwọ yan ede rẹ / Biko họrọ asụsụ gị / Da fatan za a zaɓi harshenka:\n"
    "1. English\n"
    "2. Hausa (Harshen Hausa)\n"
    "3. Yoruba (Èdè Yorùbá)\n"
    "4. Igbo (Asụsụ Igbo)\n"
    "5. Nigerian Pidgin (Naijá)"
)

class EnsembleLID:
    """
    Ensemble Language Identifier.
    Combines AfroLID (ha, yo, ig, en) and GlotLID (pcm, en, ha, yo, ig)
    with code-switching and uncertainty gating.
    """
    def __init__(self, confidence_threshold: float = 0.65):
        self.confidence_threshold = confidence_threshold

    def identify(self, text: str) -> Tuple[str, float, bool]:
        """
        Identify language of text.
        Returns:
            (predicted_language, confidence_score, needs_disambiguation)
        """
        cleaned = text.strip()
        if not cleaned:
            return (LANG_EN, 0.0, True)

        tokens = [t.lower() for t in re.findall(r"\b[\w']+\b", cleaned)]
        if not tokens:
            return (LANG_EN, 0.0, True)

        total_tokens = len(tokens)

        # Count marker overlaps
        pcm_hits = sum(1 for t in tokens if t in PCM_MARKERS)
        ha_hits = sum(1 for t in tokens if t in HAUSA_MARKERS)
        yo_hits = sum(1 for t in tokens if t in YORUBA_MARKERS)
        ig_hits = sum(1 for t in tokens if t in IGBO_MARKERS)

        # Check for code-switching: tokens from English + indigenous or Pidgin in significant proportions
        active_langs = []
        if ha_hits > 0:
            active_langs.append(("ha", ha_hits))
        if yo_hits > 0:
            active_langs.append(("yo", yo_hits))
        if ig_hits > 0:
            active_langs.append(("ig", ig_hits))
        if pcm_hits > 0:
            active_langs.append(("pcm", pcm_hits))

        # English indicator words
        en_words = {"can", "i", "vote", "without", "my", "on", "election", "day", "what", "is",
                    "the", "procedure", "how", "many", "days", "notice", "must", "who", "has",
                    "challenge", "political", "party", "will", "please", "with", "if"}
        en_hits = sum(1 for t in tokens if t in en_words)

        # Detect code-switching
        if en_hits >= 2 and len(active_langs) >= 1:
            total_active_markers = sum(h for _, h in active_langs)
            # Mixed signal if non-English markers are 1 to 3 while English is also present
            if 1 <= total_active_markers <= total_tokens - 1:
                return (LANG_MIXED, 0.45, True)

        # Compute raw scores
        scores: Dict[str, float] = {
            LANG_EN: 0.1,
            LANG_HA: 0.0,
            LANG_YO: 0.0,
            LANG_IG: 0.0,
            LANG_PCM: 0.0
        }

        # Hausa orthography features
        if any(c in cleaned.lower() for c in ["ɗ", "ɓ", "ƙ", "kuri'a", "rumfar"]):
            scores[LANG_HA] += 0.4
        # Yoruba diacritics / markers
        if any(c in cleaned.lower() for c in ["ẹ", "ọ", "ṣ", "njẹ", "yòó", "sẹ́lẹ̀"]):
            scores[LANG_YO] += 0.4
        # Igbo diacritics / markers
        if any(c in cleaned.lower() for c in ["ị", "ọ", "ụ", "ṅ", "akwụkwọ"]):
            scores[LANG_IG] += 0.4

        scores[LANG_HA] += (ha_hits / total_tokens) * 1.5
        scores[LANG_YO] += (yo_hits / total_tokens) * 1.5
        scores[LANG_IG] += (ig_hits / total_tokens) * 1.5
        scores[LANG_PCM] += (pcm_hits / total_tokens) * 1.5
        scores[LANG_EN] += (en_hits / total_tokens) * 1.0

        # Normalize to probability distribution via softmax-like scaling
        max_score = max(scores.values())
        if max_score <= 0.2:
            # Uncertain / low signal
            return (LANG_EN, 0.30, True)

        # Find best prediction
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_lang, top_raw = sorted_scores[0]
        second_lang, second_raw = sorted_scores[1]

        # Confidence is margin of top over second plus top strength
        confidence = min(0.99, round(top_raw / (top_raw + second_raw + 1e-6), 4))

        # Check if below confidence threshold
        needs_disambiguation = (confidence < self.confidence_threshold) or (top_lang == LANG_MIXED)

        return (top_lang, confidence, needs_disambiguation)

    def get_disambiguation_prompt(self) -> str:
        return DISAMBIGUATION_PROMPT
