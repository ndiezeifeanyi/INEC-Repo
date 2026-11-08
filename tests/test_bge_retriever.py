import pytest
from src.retrieval.bge_engine import BGEM3Retriever

def test_bge_retriever_default_fallback():
    retriever = BGEM3Retriever(enable_bge_m3=False, enable_reranker=False)
    status = retriever.get_status()
    assert status["bge_m3_enabled_flag"] is False
    assert status["bge_m3_active"] is False
    assert status["fallback_engine"] == "TranslationHybridRetriever"

    # Verify retrieval works via fallback
    results = retriever.retrieve("What is the qualifying age to register as a voter in Nigeria?", top_k=3)
    assert len(results) == 3
    assert results[0][0].chunk_id == "EA2026-S12-SS1"

def test_bge_retriever_graceful_missing_weights():
    # Attempting to enable BGE when weights/torch might not be configured must gracefully fallback
    retriever = BGEM3Retriever(enable_bge_m3=True, enable_reranker=True)
    status = retriever.get_status()
    assert status["bge_m3_enabled_flag"] is True
    # Either successfully active (if torch/model present) or gracefully inactive
    assert isinstance(status["bge_m3_active"], bool)

    # Retrieval must not crash
    results = retriever.retrieve("over-voting cancellation", top_k=2)
    assert len(results) >= 1

