import os
import hmac
import hashlib
import json
import pytest
from fastapi.testclient import TestClient
from src.web.app import app
from src.config import WHATSAPP_VERIFY_TOKEN
from src.web.session_store import SecureSessionStore

client = TestClient(app)

def test_meta_webhook_get_verification_success():
    """Verify Meta challenge response with matching hub.verify_token -> 200."""
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

def test_meta_webhook_post_unsigned_forbidden():
    """Unsigned request when secret is configured -> 403 Forbidden."""
    test_secret = "prod_meta_webhook_secret_2026"
    meta_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "100200300",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "+2348000000000", "phone_number_id": "123456"},
                    "contacts": [{"profile": {"name": "Voter"}, "wa_id": "2348011223344"}],
                    "messages": [{"from": "2348011223344", "id": "w1", "timestamp": "1731000000", "text": {"body": "Can I vote without PVC?"}, "type": "text"}]
                },
                "field": "messages"
            }]
        }]
    }
    headers = {"X-Test-Secret": test_secret}
    # Notice: No X-Hub-Signature-256 header sent
    response = client.post("/api/v1/webhook/whatsapp", json=meta_payload, headers=headers)
    assert response.status_code == 403
    assert "missing or invalid X-Hub-Signature-256" in response.json()["detail"]

def test_meta_webhook_post_bad_signature_forbidden():
    """Request with bad/corrupted HMAC signature -> 403 Forbidden."""
    test_secret = "prod_meta_webhook_secret_2026"
    meta_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "100200300",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "+2348000000000", "phone_number_id": "123456"},
                    "contacts": [{"profile": {"name": "Voter"}, "wa_id": "2348011223344"}],
                    "messages": [{"from": "2348011223344", "id": "w1", "timestamp": "1731000000", "text": {"body": "Can I vote without PVC?"}, "type": "text"}]
                },
                "field": "messages"
            }]
        }]
    }
    raw_body = json.dumps(meta_payload).encode("utf-8")
    headers = {
        "X-Hub-Signature-256": "sha256=0000000000000000000000000000000000000000000000000000000000000000",
        "X-Test-Secret": test_secret,
        "Content-Type": "application/json"
    }
    response = client.post("/api/v1/webhook/whatsapp", content=raw_body, headers=headers)
    assert response.status_code == 403
    assert "HMAC signature mismatch" in response.json()["detail"]

def test_meta_webhook_post_valid_signature_success():
    """Request with valid HMAC-SHA256 signature -> 200 OK."""
    test_secret = "prod_meta_webhook_secret_2026"
    meta_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "100200300",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "+2348000000000", "phone_number_id": "123456"},
                    "contacts": [{"profile": {"name": "Voter"}, "wa_id": "2348011223344"}],
                    "messages": [{"from": "2348011223344", "id": "w1", "timestamp": "1731000000", "text": {"body": "Can I vote without PVC?"}, "type": "text"}]
                },
                "field": "messages"
            }]
        }]
    }
    raw_body = json.dumps(meta_payload).encode("utf-8")
    valid_sig = "sha256=" + hmac.new(test_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    headers = {
        "X-Hub-Signature-256": valid_sig,
        "X-Test-Secret": test_secret,
        "Content-Type": "application/json"
    }
    response = client.post("/api/v1/webhook/whatsapp", content=raw_body, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data

def test_flat_json_blocked_in_production():
    """Flat-JSON payload without explicit TEST_MODE returns 400 Bad Request."""
    payload = {"From": "+2348011223344", "Body": "Hello"}
    response = client.post("/api/v1/webhook/whatsapp", json=payload)
    assert response.status_code == 400
    assert "Flat-JSON format only allowed in TEST_MODE" in response.json()["detail"]

def test_flat_json_allowed_with_test_mode_flag():
    """Flat-JSON payload with X-Test-Mode header is accepted."""
    payload = {"From": "+2348011223344", "Body": "STOP"}
    headers = {"X-Test-Mode": "true"}
    response = client.post("/api/v1/webhook/whatsapp", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "opted out" in data["reply"]
    assert data["status"] == "PURGED"

def test_sender_id_hmac_sha256_hash():
    """Sender IDs are hashed using HMAC-SHA256 with an environment secret; raw phone never persisted."""
    secret = "test_env_salt_secret_123"
    store = SecureSessionStore(salt=secret)
    raw_sender = "+2348012345678"

    session = store.get_or_create_session(raw_sender)
    expected_hmac = hmac.new(secret.encode("utf-8"), raw_sender.encode("utf-8"), hashlib.sha256).hexdigest()

    assert session["sender_hash"] == expected_hmac
    assert len(session["sender_hash"]) == 64
    assert raw_sender not in session
