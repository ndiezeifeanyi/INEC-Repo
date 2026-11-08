import hmac
import hashlib
import json
from fastapi.testclient import TestClient
from src.web.app import app
from src.config import WHATSAPP_VERIFY_TOKEN

client = TestClient(app)

def test_meta_webhook_get_verification_success():
    """Verify Meta challenge response with matching hub.verify_token."""
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": WHATSAPP_VERIFY_TOKEN,
        "hub.challenge": "1155992288"
    }
    response = client.get("/api/v1/webhook/whatsapp", params=params)
    assert response.status_code == 200
    assert response.text == "1155992288"

def test_meta_webhook_get_verification_failure():
    """Verify 403 Forbidden on invalid verify_token."""
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "wrong_token",
        "hub.challenge": "1155992288"
    }
    response = client.get("/api/v1/webhook/whatsapp", params=params)
    assert response.status_code == 403

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

def test_meta_cloud_api_nested_payload():
    """Verify parsing of official Meta WhatsApp Business Cloud API JSON payload."""
    meta_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "100200300",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "+2348000000000",
                        "phone_number_id": "123456"
                    },
                    "contacts": [{
                        "profile": {"name": "Citizen Voter"},
                        "wa_id": "2348011998877"
                    }],
                    "messages": [{
                        "from": "2348011998877",
                        "id": "wamid.HBgLMjM0ODAxMTk5ODg3NxUCMRIA",
                        "timestamp": "1731000000",
                        "text": {"body": "How many days notice must INEC give before election?"},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    response = client.post("/api/v1/webhook/whatsapp", json=meta_payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    # Raw phone number must never be leaked
    assert "2348011998877" not in json.dumps(data)
    assert len(data.get("sender_hash", "")) == 64

def test_meta_signature_verification():
    """Verify X-Hub-Signature-256 validation."""
    test_secret = "test_meta_webhook_secret_2026"
    body_dict = {"From": "+2348099112233", "Body": "Can I vote without my PVC?"}
    raw_body = json.dumps(body_dict).encode("utf-8")
    valid_sig = "sha256=" + hmac.new(test_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    # With valid signature
    headers = {
        "X-Hub-Signature-256": valid_sig,
        "X-Test-Secret": test_secret,
        "Content-Type": "application/json"
    }
    response = client.post("/api/v1/webhook/whatsapp", content=raw_body, headers=headers)
    assert response.status_code == 200

    # With invalid corrupted signature
    bad_headers = {
        "X-Hub-Signature-256": "sha256=invalidhex00000000000000000000000000000000000000000000000000000000",
        "X-Test-Secret": test_secret,
        "Content-Type": "application/json"
    }
    bad_response = client.post("/api/v1/webhook/whatsapp", content=raw_body, headers=bad_headers)
    assert bad_response.status_code == 403
