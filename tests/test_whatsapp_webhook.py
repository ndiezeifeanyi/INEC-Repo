from fastapi.testclient import TestClient
from src.web.app import app

client = TestClient(app)

def test_whatsapp_webhook_opt_out():
    payload = {
        "From": "whatsapp:+2348011223344",
        "Body": "STOP"
    }
    response = client.post("/api/v1/webhook/whatsapp", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "opted out" in data["reply"]
    assert data["status"] == "PURGED"

def test_whatsapp_webhook_language_selection():
    # User sends numeric choice '2' for Hausa
    payload = {
        "From": "whatsapp:+2348055667788",
        "Body": "2"
    }
    response = client.post("/api/v1/webhook/whatsapp", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "ha"
    assert "Hausa" in data["reply"]

def test_whatsapp_webhook_grounded_answer():
    # User asks English statutory question
    payload = {
        "From": "whatsapp:+2348099887766",
        "Body": "What is the qualifying age to register as a voter in Nigeria?"
    }
    response = client.post("/api/v1/webhook/whatsapp", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "Section 12(1)" in str(data.get("citations", [])) or "12" in data["reply"]
    # Check that raw phone number is NOT returned in response
    assert "+2348099887766" not in str(data)
    assert len(data.get("sender_hash", "")) == 64

