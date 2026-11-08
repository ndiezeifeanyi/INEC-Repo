import json
import math
import re
import requests
from typing import List, Tuple, Dict, Optional
from pathlib import Path
from src.models.chunk import LegalChunk
from src.retrieval.base import BaseRetriever
from src.retrieval.rrf import reciprocal_rank_fusion
from src.retrieval.translation_engine import TranslationEngine, TranslationResult

class RetrievalList(list):
    """List subclass preserving retrieved chunk tuples while carrying retrieval diagnostic metadata."""
    def __init__(self, items, bm25_top1=None, dense_top1=None, bm25_dense_disagree=False):
        super().__init__(items)
        self.bm25_top1 = bm25_top1
        self.dense_top1 = dense_top1
        self.bm25_dense_disagree = bm25_dense_disagree

class TranslationHybridRetriever(BaseRetriever):
    """
    Path B: Translate-to-English first, then run hybrid (BM25 + Dense) retrieval
    and fuse results using Reciprocal Rank Fusion (RRF).
    Query translation integrates an unofficial web endpoint (client=gtx) with explicit user consent,
    file-backed local caching, and a local rule-based dictionary fallback.
    """

    TRANSLATION_CONSENT_DISCLOSURE = (
        "Do not enter personal details; the third-party service may log your text. "
        "For non-English civic queries (Hausa, Yoruba, Igbo), query strings are transmitted to the "
        "unofficial Google Translate public web endpoint (client=gtx) solely to translate into English legal concepts. "
        "Sending is opt-in; when disabled, the system operates purely offline using a local civic glossary."
    )

    TRANSLATION_PROVIDER_LABEL = (
        "Unofficial Google Translate web endpoint (client=gtx, reverse-engineered public HTTP interface, "
        "unauthenticated, no SLA, subject to rate-limiting and low-resource semantic drift)."
    )

    def __init__(self, data_path: Optional[Path] = None, enable_online_translation: bool = False, cache_enabled: bool = True):
        self.chunks: List[LegalChunk] = []
        self._load_data(data_path)
        self.doc_freqs: Dict[str, int] = {}
        self.doc_lens: List[int] = []
        self.avg_doc_len = 0.0
        self.enable_online_translation = enable_online_translation
        self.cache_enabled = cache_enabled
        self.translation_engine = TranslationEngine(
            enable_online=enable_online_translation,
            cache_enabled=cache_enabled
        )
        self.cache_path = self.translation_engine.cache_path
        self.translation_cache = self.translation_engine.cache
        self._build_bm25_index()
        self.last_bm25_top1: Optional[str] = None
        self.last_dense_top1: Optional[str] = None
        self.last_bm25_dense_disagree: bool = False

    def _load_cache(self) -> Dict[str, str]:
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self):
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self.translation_cache, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

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

    def translate_query_to_english(
        self,
        query: str,
        lang: str,
        allow_online: Optional[bool] = None,
        cache_enabled: Optional[bool] = None
    ) -> str:
        """Translates low-resource queries to English legal conceptual equivalents."""
        res = self.translation_engine.translate(
            query=query,
            lang=lang,
            allow_online=allow_online,
            cache_enabled=cache_enabled
        )
        return res.translated_text


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

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        lang: str = "en",
        allow_online: Optional[bool] = None,
        cache_enabled: Optional[bool] = None
    ) -> List[Tuple[LegalChunk, float]]:
        # 1. Translate query to English
        en_query = self.translate_query_to_english(
            query, lang, allow_online=allow_online, cache_enabled=cache_enabled
        )

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

        # Disagreement check between BM25 and Dense top-1
        dense_top1 = dense_scores[0][0].chunk_id if dense_scores else None
        bm25_top1 = bm25_scores[0][0].chunk_id if bm25_scores else None
        bm25_dense_disagree = (dense_top1 != bm25_top1)
        self.last_dense_top1 = dense_top1
        self.last_bm25_top1 = bm25_top1
        self.last_bm25_dense_disagree = bm25_dense_disagree

        # 4. Reciprocal Rank Fusion
        fused = reciprocal_rank_fusion([bm25_scores, dense_scores])

        # General statutory subordination promotion rule:
        # If top-1 chunk text begins with "Subject to section <N>", and a candidate chunk with section_number == <N>
        # is present in the retrieved set, promote that governing substantive provision to top-1.
        if fused:
            top_c = fused[0][0]
            m = re.match(r"^Subject to section (\d+)", top_c.content_english.strip(), re.IGNORECASE)
            if m:
                target_sec = m.group(1)
                for idx, (c, sc) in enumerate(fused[1:], start=1):
                    if c.section_number == target_sec:
                        promoted_chunk = fused.pop(idx)
                        fused.insert(0, (promoted_chunk[0], fused[0][1] + 0.001))
                        break

        return RetrievalList(
            fused[:top_k],
            bm25_top1=bm25_top1,
            dense_top1=dense_top1,
            bm25_dense_disagree=bm25_dense_disagree
        )

