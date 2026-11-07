from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class LegalChunk(BaseModel):
    chunk_id: str
    document_title: str
    document_source_url: str
    document_sha256: str
    document_version: str
    retrieval_date: str
    part_title: str
    section_number: str
    subsection_number: Optional[str] = None
    page: Optional[int] = None
    content_english: str
    content_plain: str
    legal_status: str = Field(
        ...,
        description="'ENACTED' or 'UNCONFIRMED'"
    )

class Citation(BaseModel):
    document_title: str
    section: str
    subsection: Optional[str] = None
    version: str
    retrieval_date: str
    source_url: str
    legal_status: str

class VoterAnswer(BaseModel):
    question: str
    language: str
    answer_text: str
    answer_plain: str
    citations: List[Citation]
    retrieved_chunk_ids: List[str]
    confidence_flags: List[str] = []
    has_audio: bool = False
    audio_url: Optional[str] = None

class VerificationResult(BaseModel):
    input_item: str
    type: str  # "url" or "message"
    status: str  # "Matches an official source" | "Does not match any official source I can check" | "Can't tell"
    matched_source: Optional[str] = None
    confidence_notes: str
    corpus_size: int = 0
    corpus_last_updated: str = "2026-11-07"
    disclaimer: str = (
        "This check compares inputs against gazetted statutes and official public INEC records. "
        "It is not exhaustive or infallible and does not evaluate political opinions or non-electoral claims."
    )

