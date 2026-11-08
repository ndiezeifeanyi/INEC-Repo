import pytest
from fastapi.testclient import TestClient
from src.web.app import app

client = TestClient(app)

def test_lid_pure_english_auto_detection():
    # Pure English question about voter registration
    payload = {
        "query": "What is the qualifying age to register as a voter in Nigeria?",
        "language": "auto",
        "confirmed_language": False
    }
    response = client.post("/api/v1/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ANSWER"
    assert data["language"] == "en"
    assert "LID_AUTO_DETECTED_EN" in data["confidence_flags"]
    assert any(c.get("section") == "12" for c in data.get("citations", []))

def test_lid_pure_hausa_auto_detection():
    # Pure Hausa question
    payload = {
        "query": "Wane shekaru ne mutum zai iya yin rajistar zabe a Najeriya?",
        "language": "auto",
        "confirmed_language": False
    }
    response = client.post("/api/v1/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ANSWER"
    assert data["language"] == "ha"
    assert "LID_AUTO_DETECTED_HA" in data["confidence_flags"]

def test_lid_pidgin_requires_confirmation():
    # Nigerian Pidgin question must trigger confirmation
    payload = {
        "query": "Wetin go happen if vote plenty pass people wey BVAS scan for polling unit?",
        "language": "auto",
        "confirmed_language": False
    }
    response = client.post("/api/v1/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "NEEDS_LANGUAGE_CONFIRMATION"
    assert "Please confirm your language" in data["disambiguation_prompt"]
    assert "NEEDS_LANGUAGE_CONFIRMATION" in data["confidence_flags"]

def test_lid_code_switched_requires_confirmation():
    # Code-switched query: English + Igbo/Pidgin markers
    payload = {
        "query": "Abeg can I vote with temporary slip kwanu if PVC no dey?",
        "language": "auto",
        "confirmed_language": False
    }
    response = client.post("/api/v1/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "NEEDS_LANGUAGE_CONFIRMATION"
    assert "Nigerian Pidgin" in data["disambiguation_prompt"]

def test_lid_confirmed_pidgin_passthrough():
    # Once user explicitly confirms Nigerian Pidgin ('pcm')
    payload = {
        "query": "Wetin go happen if vote plenty pass people wey BVAS scan for polling unit?",
        "language": "pcm",
        "confirmed_language": True
    }
    response = client.post("/api/v1/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ANSWER"
    assert data["language"] == "pcm"
    assert "EXPERIMENTAL_PIDGIN_PASSTHROUGH" in data["confidence_flags"]
    assert len(data["citations"]) > 0

def test_lid_confirmed_override():
    # Voter explicitly selects Hausa with confirmed_language=True
    payload = {
        "query": "Can I vote without PVC?",
        "language": "ha",
        "confirmed_language": True
    }
    response = client.post("/api/v1/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ANSWER"
    assert data["language"] == "ha"
