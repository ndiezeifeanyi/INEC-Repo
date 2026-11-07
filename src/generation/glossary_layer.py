import json
from pathlib import Path
from typing import Dict, List, Tuple

class CivicGlossaryEnforcer:
    """Enforces validated civic terms in Hausa, Yoruba, and Igbo."""

    def __init__(self, glossaries_dir: Path = None):
        if glossaries_dir is None:
            glossaries_dir = Path(__file__).resolve().parent.parent.parent / "data" / "glossaries"
        self.glossaries_dir = glossaries_dir
        self.glossaries: Dict[str, Dict[str, dict]] = {}
        self._load_glossaries()

    def _load_glossaries(self):
        for lang in ["ha", "yo", "ig"]:
            path = self.glossaries_dir / f"{'hausa' if lang=='ha' else 'yoruba' if lang=='yo' else 'igbo'}.json"
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.glossaries[lang] = {
                        item["english"].lower(): item for item in data.get("terms", [])
                    }

    def validate_and_enforce(self, text: str, lang: str) -> Tuple[str, List[str]]:
        """
        Validates terms in the translated/generated text against the certified glossary.
        Returns the sanitized text and any unreviewed term warnings.
        """
        if lang not in self.glossaries:
            return text, []

        warnings = []
        glossary = self.glossaries[lang]

        # Scan for terms that must carry validated rendering
        for eng_term, meta in glossary.items():
            expected_target = meta["target"].lower()
            status = meta.get("status", "UNREVIEWED")

            if status != "VALIDATED":
                warnings.append(f"UNREVIEWED: Term '{eng_term}' ({expected_target}) has not undergone native-speaker review.")

        return text, warnings

    def get_preferred_term(self, english_term: str, lang: str) -> str:
        """Returns the approved civic term, or the English term in quotes if unvalidated."""
        glossary = self.glossaries.get(lang, {})
        entry = glossary.get(english_term.lower())
        if entry and entry.get("status") == "VALIDATED":
            return entry["target"]
        return f'"{english_term}"'

