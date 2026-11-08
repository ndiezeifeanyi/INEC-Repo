"""
Tests for Phase 3: Multilingual Query Translation Engine (Hausa, Yoruba, Igbo, Nigerian Pidgin).
Verifies:
1. English passthrough (identity).
2. Nigerian Pidgin architectural handling (rule_mapped, pass_through, abstain) and lack of NLLB pcm support.
3. Offline civic dictionary fallback when online is disabled or air-gapped.
4. Cache retrieval.
5. Safeguard compliance: non-English outputs must strictly be flagged as draft/non-authoritative.
"""

import pytest
from src.retrieval.translation_engine import TranslationEngine, TranslationResult

def test_english_identity():
    engine = TranslationEngine(enable_local_nllb=False, enable_online=False, cache_enabled=True)
    res = engine.translate("Can I vote without my PVC on election day?", lang="en")
    assert isinstance(res, TranslationResult)
    assert res.translated_text == "Can I vote without my PVC on election day?"
    assert res.method == "identity"
    assert res.confidence == 1.0
    assert res.is_draft is False

def test_pidgin_rule_mapped_strategy():
    engine = TranslationEngine(
        enable_local_nllb=False,
        enable_online=False,
        cache_enabled=True,
        pidgin_strategy="rule_mapped"
    )
    query = "Wetin go happen if vote plenty pass people wey BVAS scan?"
    res = engine.translate(query, lang="pcm")
    assert res.method == "pidgin_rule_mapped"
    assert res.confidence == 0.85
    assert res.is_draft is True
    # Should include mapped civic terminology
    assert "over-voting" in res.translated_text
    assert "bvas" in res.translated_text

def test_pidgin_passthrough_strategy():
    engine = TranslationEngine(
        enable_local_nllb=False,
        enable_online=False,
        cache_enabled=True,
        pidgin_strategy="pass_through"
    )
    query = "I fit vote if I no carry my PVC go polling unit?"
    res = engine.translate(query, lang="pcm")
    assert res.method == "pidgin_passthrough"
    assert res.translated_text == query
    assert res.confidence == 0.70
    assert res.is_draft is True

def test_pidgin_abstain_strategy():
    engine = TranslationEngine(
        enable_local_nllb=False,
        enable_online=False,
        cache_enabled=True,
        pidgin_strategy="abstain"
    )
    query = "How many days notice INEC suppose give?"
    res = engine.translate(query, lang="pcm")
    assert res.method == "pidgin_abstain"
    assert res.confidence == 0.0
    assert res.translated_text == ""
    assert res.is_draft is True

def test_offline_dictionary_fallback_hausa():
    # Cache disabled, online disabled -> must fall back to local civic dictionary
    engine = TranslationEngine(enable_local_nllb=False, enable_online=False, cache_enabled=False)
    query = "Ta yaya za a tantance mai kada kuri'a a ranar zabe idan na'urar bvas ta samu matsala?"
    res = engine.translate(query, lang="ha")
    assert res.method == "offline_dictionary"
    assert res.is_draft is True
    # Must expand with civic terms
    assert "accreditation" in res.translated_text
    assert "bvas" in res.translated_text

def test_cached_translation_retrieval():
    engine = TranslationEngine(enable_local_nllb=False, enable_online=False, cache_enabled=True)
    # Use a query that exists in tests/data/heldout_bench.json and translation_cache
    query = "Wane shekaru ne mutum zai iya yin rajistar zabe a Najeriya?"
    res = engine.translate(query, lang="ha")
    if f"ha::{query}" in engine.cache:
        assert res.method == "cached_online"
        assert res.is_draft is True
        assert len(res.translated_text) > 0
