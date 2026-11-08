"""
src/web/session_store.py

Privacy-Preserving Session Store for WhatsApp/SMS Voter Interactions.
Strict Privacy Guarantees:
1. ONLY stores a salted SHA-256 hash of the sender ID.
2. NEVER stores message text, query strings, personal identity details, or audio bytes.
3. Automatically enforces a 24-hour TTL expiration.
4. Immediate complete purge upon receiving opt-out / STOP command.
"""

import os
import time
import hashlib
from typing import Optional, Dict, Any

SESSION_SALT = os.environ.get("SESSION_SALT", "inec_hackathon_track3_salt_2026_audit")
SESSION_TTL_SECONDS = 24 * 3600  # 24 hours

class SecureSessionStore:
    """In-memory TTL session store with salted cryptographic sender hashing."""

    def __init__(self, salt: str = SESSION_SALT, ttl_seconds: int = SESSION_TTL_SECONDS):
        self.salt = salt
        self.ttl = ttl_seconds
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def _hash_sender(self, raw_sender_id: str) -> str:
        """Computes one-way salted SHA-256 hash. Raw sender ID is never persisted."""
        normalized = raw_sender_id.strip()
        salted = f"{self.salt}:{normalized}".encode("utf-8")
        return hashlib.sha256(salted).hexdigest()

    def get_or_create_session(self, raw_sender_id: str) -> Dict[str, Any]:
        """
        Retrieves active session or creates a new one.
        Enforces TTL expiration.
        """
        sender_hash = self._hash_sender(raw_sender_id)
        current_time = time.time()

        # Check existing session and purge if expired
        if sender_hash in self._sessions:
            session = self._sessions[sender_hash]
            if current_time - session["last_active"] > self.ttl:
                del self._sessions[sender_hash]
            else:
                session["last_active"] = current_time
                session["interaction_count"] += 1
                return session

        # Create new minimalist privacy-compliant session record
        new_session = {
            "sender_hash": sender_hash,
            "detected_language": "en",
            "language_confirmed": False,
            "created_at": current_time,
            "last_active": current_time,
            "interaction_count": 1
        }
        self._sessions[sender_hash] = new_session
        return new_session

    def update_language(self, raw_sender_id: str, language: str, confirmed: bool = True):
        session = self.get_or_create_session(raw_sender_id)
        session["detected_language"] = language
        session["language_confirmed"] = confirmed
        session["last_active"] = time.time()

    def purge_sender(self, raw_sender_id: str) -> bool:
        """Immediate complete deletion of sender session upon STOP / opt-out."""
        sender_hash = self._hash_sender(raw_sender_id)
        if sender_hash in self._sessions:
            del self._sessions[sender_hash]
            return True
        return False

    def prune_expired(self) -> int:
        """Prunes all sessions exceeding 24h TTL."""
        current_time = time.time()
        expired = [h for h, s in self._sessions.items() if current_time - s["last_active"] > self.ttl]
        for h in expired:
            del self._sessions[h]
        return len(expired)

    def count_active_sessions(self) -> int:
        self.prune_expired()
        return len(self._sessions)
