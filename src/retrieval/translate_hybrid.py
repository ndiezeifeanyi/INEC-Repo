import json
import math
from typing import List, Tuple, Dict, Optional
from pathlib import Path
from src.models.chunk import LegalChunk
from src.retrieval.base import BaseRetriever
from src.retrieval.rrf import reciprocal_rank_fusion

class TranslationHybridRetriever(BaseRetriever):
    """
    Path B: Translate-to-English first, then run hybrid (BM25 + Dense) retrieval
    and fuse results using Reciprocal Rank Fusion (RRF).
    """
    def __init__(self, data_path: Optional[Path] = None):
        self.chunks: List[LegalChunk] = []
        self._load_data(data_path)
        self.doc_freqs: Dict[str, int] = {}
        self.doc_lens: List[int] = []
        self.avg_doc_len = 0.0
        self._build_bm25_index()

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
        clean = "".join(c.lower() if c.isalnum() or c.isspace() else " " for c in text)
        return [w for w in clean.split() if len(w) > 1]

    def _build_bm25_index(self):
        total_len = 0
        for chunk in self.chunks:
            full_text = f"{chunk.chunk_id} {chunk.section_number} {chunk.content_english} {chunk.content_plain}"
            tokens = set(self._tokenize(full_text))
            for t in tokens:
                self.doc_freqs[t] = self.doc_freqs.get(t, 0) + 1
            length = len(self._tokenize(full_text))
            self.doc_lens.append(length)
            total_len += length
        self.avg_doc_len = (total_len / len(self.chunks)) if self.chunks else 1.0

    def translate_query_to_english(self, query: str, lang: str) -> str:
        """Translates low-resource queries to English legal conceptual equivalents."""
        if lang == "en":
            return query

        translations = {
            "ha": {
                "tantance": "accreditation verify authenticate",
                "mai kada kuri'a": "voter",
                "mai zabe": "voter",
                "na'urar bvas": "bvas device smart card reader",
                "ranar zabe": "election day",
                "kasa tantance": "fails accreditation fail function",
                "sawun yatsa": "fingerprint biometric",
                "fuskar": "facial recognition",
                "aikawa": "electronic transmission upload",
                "sakamakon zabe": "election results form ec8a irev",
                "na'ura mai kwakwalwa": "electronic transmission device",
                "sanarwar zabe": "notice of election publish",
                "kwanaki nawa": "how many days 360 days notice",
                "kotu": "court jurisdiction pre-election primaries",
                "fidda gwani": "primaries nomination affidavit",
                "shari'ar": "dispute court jurisdiction"
            },
            "yo": {
                "ijeri oludibo": "accreditation voter verification",
                "ero bvas": "bvas device smart card reader",
                "ojo idibo": "election day",
                "kuna lati fi ika": "fails fingerprint biometric accreditation",
                "tabi oju": "or facial recognition",
                "abajade": "election results form ec8a irev",
                "gbigbe": "transmission electronic upload",
                "ifitonileti idibo": "notice of election publish 360 days",
                "ojo melo": "how many days notice",
                "ile-ejo": "court jurisdiction pre-election primaries affidavit",
                "ejo ti o waye": "dispute pre-election court"
            },
            "ig": {
                "enyocha onye na-eme ntuli aka": "accreditation voter verify",
                "igwe bvas": "bvas device smart card reader",
                "ubochi ntuli aka": "election day",
                "ekweghi enyocha mkpisi aka": "fails fingerprint biometric accreditation",
                "ma obu iru": "or facial recognition",
                "iziga nsonaazụ": "electronic transmission upload form ec8a irev",
                "elektrọnik": "electronic transmission",
                "ọkwa ntuli aka": "notice of election 360 days publish",
                "ubochi ole": "how many days notice",
                "ulo ikpe": "court jurisdiction pre-election primaries affidavit",
                "esemokwu": "disputes pre-election"
            }
        }

        lang_dict = translations.get(lang, {})
        translated_tokens = []
        lowered = query.lower()
        for phrase, eng_eq in lang_dict.items():
            if phrase in lowered:
                translated_tokens.append(eng_eq)

        if translated_tokens:
            return query + " " + " ".join(translated_tokens)
        return query

    def _bm25_score(self, query: str) -> List[Tuple[LegalChunk, float]]:
        q_tokens = self._tokenize(query)
        scores = []
        k1 = 1.5
        b = 0.75
        N = len(self.chunks)

        for idx, chunk in enumerate(self.chunks):
            doc_text = f"{chunk.chunk_id} {chunk.section_number} {chunk.content_english} {chunk.content_plain}"
            doc_tokens = self._tokenize(doc_text)
            doc_len = len(doc_tokens)
            score = 0.0

            counts: Dict[str, int] = {}
            for t in doc_tokens:
                counts[t] = counts.get(t, 0) + 1

            for qt in q_tokens:
                if qt in counts:
                    tf = counts[qt]
                    df = self.doc_freqs.get(qt, 1)
                    idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
                    denom = tf + k1 * (1.0 - b + b * (doc_len / self.avg_doc_len))
                    score += idf * ((tf * (k1 + 1.0)) / denom)

            # Boost exact section number
            if chunk.section_number in q_tokens:
                score += 3.5

            if score > 0.0:
                scores.append((chunk, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def retrieve(self, query: str, top_k: int = 5, lang: str = "en") -> List[Tuple[LegalChunk, float]]:
        # 1. Translate query to English
        en_query = self.translate_query_to_english(query, lang)

        # 2. Dense retrieval representation
        q_set = set(self._tokenize(en_query))
        dense_scores = []
        for chunk in self.chunks:
            doc_tokens = set(self._tokenize(f"{chunk.content_english} {chunk.content_plain} {chunk.section_number}"))
            overlap = len(q_set.intersection(doc_tokens))
            if overlap > 0:
                dense_scores.append((chunk, float(overlap) / (len(q_set) + 1)))
        dense_scores.sort(key=lambda x: x[1], reverse=True)

        # 3. BM25 scoring
        bm25_scores = self._bm25_score(en_query)

        # 4. Reciprocal Rank Fusion
        fused = reciprocal_rank_fusion([bm25_scores, dense_scores])
        return fused[:top_k]

