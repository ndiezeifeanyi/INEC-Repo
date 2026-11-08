import pytest
from src.lid.ensemble_lid import EnsembleLID, LANG_EN, LANG_HA, LANG_YO, LANG_IG, LANG_PCM, LANG_MIXED
from src.config import LID_CONFIDENCE_THRESHOLD

def test_lid_threshold_calibrated():
    assert LID_CONFIDENCE_THRESHOLD == 0.75

def test_lid_pure_english():
    lid = EnsembleLID(confidence_threshold=LID_CONFIDENCE_THRESHOLD)
    lang, conf, needs_disambig = lid.identify("How many days notice must INEC publish before the election?")
    assert lang == LANG_EN
    assert conf >= 0.75
    assert needs_disambig is False

def test_lid_pure_hausa():
    lid = EnsembleLID(confidence_threshold=LID_CONFIDENCE_THRESHOLD)
    lang, conf, needs_disambig = lid.identify("Zan iya kada kuri'a ba tare da katin zabe na dindindin ba?")
    assert lang == LANG_HA
    assert conf >= 0.75
    assert needs_disambig is False

def test_lid_pidgin_requires_disambiguation():
    lid = EnsembleLID(confidence_threshold=LID_CONFIDENCE_THRESHOLD)
    lang, conf, needs_disambig = lid.identify("Wetin go happen if vote plenty pass people wey BVAS scan?")
    # Pidgin and code-switched queries must require disambiguation
    assert needs_disambig is True

def test_lid_code_switched_detection():
    lid = EnsembleLID(confidence_threshold=LID_CONFIDENCE_THRESHOLD)
    lang, conf, needs_disambig = lid.identify("Abeg can I vote with temporary slip kwanu if PVC no dey?")
    assert lang == LANG_MIXED
    assert needs_disambig is True
    prompt = lid.get_disambiguation_prompt()
    assert "Please confirm your language" in prompt
    assert "Nigerian Pidgin" in prompt

