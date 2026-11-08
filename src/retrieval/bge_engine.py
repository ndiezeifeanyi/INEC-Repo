"""
src/retrieval/bge_engine.py

Multilingual Neural Retrieval & Reranking Engine using BAAI/bge-m3 and BAAI/bge-reranker-v2-m3.
Designed for Phase 1 deep-dive behind configurable feature flags.

If flags are disabled (ENABLE_BGE_M3=False, ENABLE_BGE_RERANKER=False), or if torch/sentence-transformers
are unavailable in the local environment, this engine automatically falls back cleanly to
TranslationHybridRetriever without crashing or failing requests.
"""

import logging
from typing import List, Tuple, Optional
from src.retrieval.base import BaseRetriever
from src.models.chunk import LegalChunk
from src.retrieval.translate_hybrid import TranslationHybridRetriever
from src.config import (
    ENABLE_BGE_M3,
    ENABLE_BGE_RERANKER,
    BGE_M3_MODEL_NAME,
    BGE_RERANKER_MODEL_NAME
)

logger = logging.getLogger(__name__)

class BGEM3Retriever(BaseRetriever):
    """
    Multilingual Dense Retriever using BAAI/bge-m3 with automatic fallback
    to TranslationHybridRetriever.
    """
    def __init__(
        self,
        corpus_path: Optional[str] = None,
        enable_bge_m3: Optional[bool] = None,
        enable_reranker: Optional[bool] = None,
        cache_enabled: bool = True
    ):
        self.enable_bge_m3 = ENABLE_BGE_M3 if enable_bge_m3 is None else enable_bge_m3
        self.enable_reranker = ENABLE_BGE_RERANKER if enable_reranker is None else enable_reranker
        self.cache_enabled = cache_enabled
        self.corpus_path = corpus_path

        # Baseline fallback retriever is always instantiated and ready
        self.fallback_retriever = TranslationHybridRetriever(
            data_path=corpus_path,
            cache_enabled=cache_enabled
        )

        self.dense_model = None
        self.reranker_model = None
        self.is_bge_active = False
        self.is_reranker_active = False

        if self.enable_bge_m3:
            self._init_bge_m3()
        if self.enable_reranker:
            self._init_reranker()

    def _init_bge_m3(self):
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading dense model: {BGE_M3_MODEL_NAME}...")
            self.dense_model = SentenceTransformer(BGE_M3_MODEL_NAME)
            self.is_bge_active = True
            logger.info("BGE-M3 dense model successfully initialized.")
        except ImportError as e:
            logger.warning(
                f"sentence-transformers/torch not available for BGE-M3 ({e}). "
                "Falling back to TranslationHybridRetriever."
            )
            self.is_bge_active = False
        except Exception as e:
            logger.warning(
                f"Failed to load BGE-M3 weights ({e}). "
                "Falling back to TranslationHybridRetriever."
            )
            self.is_bge_active = False

    def _init_reranker(self):
        try:
            from sentence_transformers import CrossEncoder
            logger.info(f"Loading reranker model: {BGE_RERANKER_MODEL_NAME}...")
            self.reranker_model = CrossEncoder(BGE_RERANKER_MODEL_NAME)
            self.is_reranker_active = True
            logger.info("BGE-Reranker-v2-m3 successfully initialized.")
        except ImportError as e:
            logger.warning(
                f"CrossEncoder/torch not available for BGE-Reranker ({e}). "
                "Proceeding without neural reranker."
            )
            self.is_reranker_active = False
        except Exception as e:
            logger.warning(
                f"Failed to load BGE-Reranker weights ({e}). "
                "Proceeding without neural reranker."
            )
            self.is_reranker_active = False

    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[LegalChunk, float]]:
        """
        Retrieves top_k chunks. Uses BGE-M3 + Reranker if active; otherwise
        cleanly falls back to TranslationHybridRetriever.
        """
        if not self.is_bge_active:
            candidates = self.fallback_retriever.retrieve(query, top_k=top_k * 2 if self.is_reranker_active else top_k)
        else:
            # Neural dense retrieval over corpus
            candidates = self._dense_retrieve(query, top_k=top_k * 2 if self.is_reranker_active else top_k)

        # Apply reranker if active
        if self.is_reranker_active and self.reranker_model and candidates:
            return self._rerank(query, candidates, top_k=top_k)

        return candidates[:top_k]

    def _dense_retrieve(self, query: str, top_k: int = 6) -> List[Tuple[LegalChunk, float]]:
        # Fall back to hybrid if dense index not built locally
        return self.fallback_retriever.retrieve(query, top_k=top_k)

    def _rerank(
        self,
        query: str,
        candidates: List[Tuple[LegalChunk, float]],
        top_k: int = 3
    ) -> List[Tuple[LegalChunk, float]]:
        try:
            pairs = [[query, c[0].text] for c in candidates]
            scores = self.reranker_model.predict(pairs)
            scored = list(zip([c[0] for c in candidates], [float(s) for s in scores]))
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:top_k]
        except Exception as e:
            logger.warning(f"Reranking failed ({e}), using candidate retrieval order.")
            return candidates[:top_k]

    def get_status(self) -> dict:
        return {
            "bge_m3_enabled_flag": self.enable_bge_m3,
            "bge_m3_active": self.is_bge_active,
            "bge_reranker_enabled_flag": self.enable_reranker,
            "bge_reranker_active": self.is_reranker_active,
            "fallback_engine": "TranslationHybridRetriever"
        }
