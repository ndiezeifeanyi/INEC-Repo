import time
import pytest
from src.web.session_store import SecureSessionStore

def test_sender_id_salted_hash_privacy():
    store = SecureSessionStore(salt="test_salt_secret")
    raw_phone = "+2348039998888"

    session = store.get_or_create_session(raw_phone)
    sender_hash = session["sender_hash"]

    # Verify sender_hash is a 64-character SHA-256 hex string
    assert len(sender_hash) == 64
    assert raw_phone not in sender_hash

    # Verify internal dictionary stores only the hash, never the raw phone number
    assert sender_hash in store._sessions
    assert raw_phone not in store._sessions

    # Verify zero message content is stored
    assert "query" not in session
    assert "message" not in session
    assert "body" not in session
    assert "audio" not in session

def test_session_ttl_expiration():
    # Test with 1-second TTL
    store = SecureSessionStore(salt="test_salt", ttl_seconds=1)
    raw_phone = "+2347011112222"

    store.get_or_create_session(raw_phone)
    assert store.count_active_sessions() == 1

    time.sleep(1.2)
    # After TTL, session must expire and be pruned
    assert store.count_active_sessions() == 0

def test_session_stop_purge():
    store = SecureSessionStore(salt="test_salt")
    raw_phone = "+2349022223333"

    store.get_or_create_session(raw_phone)
    assert store.count_active_sessions() == 1

    purged = store.purge_sender(raw_phone)
    assert purged is True
    assert store.count_active_sessions() == 0
