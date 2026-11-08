import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient
from src.web.app import app

client = TestClient(app)

def test_api_health():
    """Verify /health endpoint returns healthy status and active corpus count."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["corpus_chunks"] > 0
    assert data["official_domains"] >= 3
    assert data["known_fakes"] >= 2

def test_api_v1_ask_grounded():
    """Verify /api/v1/ask retrieves official Electoral Act provisions and citations."""
    payload = {
        "query": "What are the rules regarding over-voting when votes cast exceed accredited voters?",
        "language": "en"
    }
    response = client.post("/api/v1/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer_text" in data
    assert len(data["citations"]) > 0
    # Must cite Section 51
    sections = [c["section"] for c in data["citations"]]
    assert any("51" in s for s in sections)

def test_api_v1_ask_empty_query():
    """Verify empty query returns 400."""
    response = client.post("/api/v1/ask", json={"query": "   ", "language": "en"})
    assert response.status_code == 400

def test_api_check_official_link():
    """Verify /check and /api/v1/check verify official INEC domain."""
    for endpoint in ["/check", "/api/v1/check"]:
        response = client.post(endpoint, json={"item": "https://cvr.inecnigeria.org/register"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Matches an official source"
        assert "cvr.inecnigeria.org" in data["matched_source"]

def test_api_check_known_fake():
    """Verify /check flags known scam domains."""
    response = client.post("/check", json={"item": "http://linksnapro.com/cvrreg"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Does not match any official source I can check"
    assert "linksnapro.com" in data["confidence_notes"]
