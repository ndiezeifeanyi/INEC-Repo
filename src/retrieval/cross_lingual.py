import json
import math
from typing import List, Tuple, Dict, Optional
from pathlib import Path
from src.models.chunk import LegalChunk
from src.retrieval.base import BaseRetriever

class CrossLingualRetriever(BaseRetriever):
    """
    Path A: Cross-lingual retrieval directly comparing Hausa, Yoruba, Igbo, and English
    queries against legal corpus vectors.
    """
    def __init__(self, data_path: Optional[Path] = None):
        self.chunks: List[LegalChunk] = []
        self._load_data(data_path)

    def _load_data(self, data_path: Optional[Path] = None):
        if data_path is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            files = [
                base_dir / "data" / "processed" / "electoral_act_2026.jsonl",
                base_dir / "data" / "processed" / "inec_transmission_procedure.jsonl"
            ]
        else:
            files = [data_path]

        for f in files:
            if f.exists():
                with open(f, "r", encoding="utf-8") as fh:
                    for line in fh:
                        if line.strip():
                            chunk_data = json.loads(line)
                            self.chunks.append(LegalChunk(**chunk_data))

    def _tokenize(self, text: str) -> List[str]:
        # Normalization and simple n-gram tokenization
        clean = "".join(c.lower() if c.isalnum() or c.isspace() else " " for c in text)
        return [w for w in clean.split() if len(w) > 1]

    def retrieve(self, query: str, top_k: int = 5, lang: str = "en") -> List[Tuple[LegalChunk, float]]:
        # Map common indigenous civic terms to statutory concepts
        synonym_map = {
            "tantance": "accreditation bvas verify",
            "kuri'a": "vote ballot",
            "zabe": "election polling",
            "rumfa": "polling unit",
            "ijeri": "accreditation bvas verify",
            "ibudo": "polling unit",
            "apoti": "ballot box",
            "enyocha": "accreditation bvas verify",
            "ntuli": "election voting",
            "vootu": "ballot vote",
            "bvas": "bvas electronic smart card reader technological device",
            "transmiss": "transmission transmit upload result irev",
            "aikawa": "transmission transmit upload irev",
            "gbigbe": "transmission transmit upload irev",
            "iziga": "transmission transmit upload irev",
            "notice": "notice 360 days publish",
            "sanarwa": "notice 360 days publish",
            "ifitonileti": "notice 360 days publish",
            "okwa": "notice 360 days publish",
            "pre-election": "pre-election primaries affidavit court jurisdiction",
            "fidda": "primaries pre-election court jurisdiction",
            "saaju": "pre-election primaries court jurisdiction",
            "esemokwu": "pre-election primaries court jurisdiction"
        }

        q_tokens = self._tokenize(query)
        expanded_query = list(q_tokens)
        for t in q_tokens:
            if t in synonym_map:
                expanded_query.extend(synonym_map[t].split())

        scored: List[Tuple[LegalChunk, float]] = []
        q_set = set(expanded_query)

        for chunk in self.chunks:
            # Score against section numbers, english content, plain text, and chunk_id
            doc_text = f"{chunk.chunk_id} {chunk.section_number} {chunk.content_english} {chunk.content_plain}".lower()
            doc_tokens = self._tokenize(doc_text)
            doc_set = set(doc_tokens)

            overlap = len(q_set.intersection(doc_set))
            # Exact section match bonus
            section_bonus = 3.0 if chunk.section_number in q_tokens else 0.0
            # Jaccard + Overlap density score
            score = (overlap / (math.sqrt(len(q_set) + 1) * math.sqrt(len(doc_set) + 1))) + section_bonus
            if score > 0.0:
                scored.append((chunk, float(score)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

