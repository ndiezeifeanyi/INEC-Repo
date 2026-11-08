from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pathlib import Path
from typing import Optional, List

from src.models.chunk import VoterAnswer, VerificationResult
from src.retrieval.translate_hybrid import TranslationHybridRetriever
from src.retrieval.cross_lingual import CrossLingualRetriever
from src.generation.prompt_builder import GroundedAnswerGenerator
from src.verification.matcher import OfficialSourceChecker
from src.speech.tts_engine import MMSTTSEngine

app = FastAPI(
    title="INEC Multilingual Civic QA & Verifier",
    description="Independent, nonpartisan civic tech prototype strictly answering from Electoral Act 2026 & verifying links.",
    version="0.1.0"
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "src" / "web" / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "src" / "web" / "static")), name="static")

# Initialize engines
retriever = TranslationHybridRetriever()
generator = GroundedAnswerGenerator()
checker = OfficialSourceChecker()

class AskRequest(BaseModel):
    query: str
    language: str = "en"  # en, ha, yo, ig
    allow_translation: bool = False

class CheckRequest(BaseModel):
    item: str

from src.config import OFFICIAL_INEC_DOMAINS, KNOWN_FAKE_DOMAINS

@app.get("/health")
async def health_check():
    """Service health and corpus readiness check."""
    loaded_files = [
        "data/processed/electoral_act_2026.jsonl",
        "data/processed/inec_transmission_procedure.jsonl",
        "data/processed/inec_bulletins.jsonl"
    ]
    electoral_act_chunks = sum(1 for c in retriever.chunks if "EA2026" in c.chunk_id)
    transmission_chunks = sum(1 for c in retriever.chunks if "INEC2026-ET" in c.chunk_id)
    bulletin_records = len(checker.bulletins)
    total_chunks = len(retriever.chunks) + bulletin_records

    return {
        "status": "healthy",
        "service": "INEC Multilingual Civic QA & Verifier",
        "corpus_chunks": len(retriever.chunks),
        "total_corpus_records": total_chunks,
        "breakdown": {
            "electoral_act_chunks": electoral_act_chunks,
            "transmission_procedure_chunks": transmission_chunks,
            "verification_bulletin_records": bulletin_records,
            "total_indexed_retrieval_chunks": len(retriever.chunks)
        },
        "files_loaded": loaded_files,
        "official_domains": len(OFFICIAL_INEC_DOMAINS),
        "known_fakes": len(KNOWN_FAKE_DOMAINS)
    }

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/api/v1/ask", response_model=VoterAnswer)
async def ask_election_rule(req: AskRequest):
    """Answers voter questions strictly grounded in Electoral Act 2026 & INEC Guidelines."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    lang = req.language.lower()
    if lang not in ["en", "ha", "yo", "ig"]:
        lang = "en"

    # Retrieve chunks (with user opt-in flag for online gtx endpoint)
    retrieved = retriever.retrieve(req.query, top_k=3, lang=lang, allow_online=req.allow_translation)
    disagree = getattr(retrieved, "bm25_dense_disagree", getattr(retriever, "last_bm25_dense_disagree", False))

    # Generate grounded response with citations
    answer = generator.generate_answer(req.query, retrieved, lang=lang, bm25_dense_disagree=disagree)
    return answer

@app.post("/check", response_model=VerificationResult)
@app.post("/api/v1/check", response_model=VerificationResult)
async def check_link_or_message(req: CheckRequest):
    """Verifies whether a link or message matches official published INEC records."""
    if not req.item.strip():
        raise HTTPException(status_code=400, detail="Item cannot be empty.")
    
    result = checker.verify(req.item)
    return result

@app.get("/api/v1/tts")
async def generate_speech(text: str, lang: str = "en"):
    """Generates audio for playback (test tone only; offline synthetic tone generator)."""
    audio_bytes = MMSTTSEngine.generate_synthetic_audio(text, lang)
    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={
            "X-License": "Audio test tone only (synthetic PCM tone generator)",
            "Cache-Control": "public, max-age=86400"
        }
    )

@app.get("/api/v1/health")
async def api_health_check():
    return {
        "status": "HEALTHY",
        "statutes": ["Electoral Act 2026", "INEC Guidelines 2026"],
        "section_29a_status": "UNCONFIRMED",
        "supported_languages": ["en", "ha", "yo", "ig", "pcm"],
        "lid_engine": "AfroLID + GlotLID Ensemble",
        "session_privacy": "Salted SHA-256 Hash + 24h TTL",
        "live_inec_access": False,
        "pii_logging": False
    }

from src.web.session_store import SecureSessionStore
from src.lid.ensemble_lid import EnsembleLID, DISAMBIGUATION_PROMPT

session_store = SecureSessionStore()
lid_detector = EnsembleLID()

class WhatsAppWebhookPayload(BaseModel):
    From: str
    Body: str
    ProfileName: Optional[str] = None

@app.post("/api/v1/webhook/whatsapp")
async def whatsapp_webhook(payload: WhatsAppWebhookPayload):
    """
    Mock-tested WhatsApp Webhook.
    Guarantees:
    - Never stores or logs raw phone number (stores only salted SHA-256 hash).
    - Never stores raw message body or audio.
    - Automatic 24-hour TTL expiration.
    - Immediate complete purge on STOP/CANCEL.
    """
    body = payload.Body.strip()
    sender = payload.From.strip()

    # 1. Check opt-out commands
    if body.upper() in ["STOP", "UNSUBSCRIBE", "CANCEL", "OPT OUT"]:
        session_store.purge_sender(sender)
        return {
            "reply": "You have opted out. Your session and data have been completely purged from memory.",
            "status": "PURGED",
            "active_sessions": session_store.count_active_sessions()
        }

    # 2. Retrieve or create session (stores only salted hash)
    session = session_store.get_or_create_session(sender)

    # 3. Check language selection numeric shortcuts
    lang_map = {"1": "en", "2": "ha", "3": "yo", "4": "ig", "5": "pcm"}
    if body in lang_map:
        selected_lang = lang_map[body]
        session_store.update_language(sender, selected_lang, confirmed=True)
        names = {"en": "English", "ha": "Hausa", "yo": "Yoruba", "ig": "Igbo", "pcm": "Nigerian Pidgin"}
        return {
            "reply": f"Language confirmed as {names[selected_lang]}. Please ask your election question.",
            "language": selected_lang,
            "session_active": True
        }

    # 4. Check if language needs confirmation via LID
    if not session.get("language_confirmed", False):
        detected_lang, conf, needs_disambig = lid_detector.identify(body)
        if needs_disambig:
            return {
                "reply": DISAMBIGUATION_PROMPT,
                "needs_disambiguation": True,
                "detected_candidate": detected_lang,
                "confidence": conf
            }
        else:
            session_store.update_language(sender, detected_lang, confirmed=True)
            active_lang = detected_lang
    else:
        active_lang = session.get("detected_language", "en")

    # 5. Retrieve answer strictly grounded in Electoral Act 2026
    lang_for_retriever = active_lang if active_lang in ["en", "ha", "yo", "ig"] else "en"
    retrieved = retriever.retrieve(body, top_k=3, lang=lang_for_retriever, allow_online=False)
    disagree = getattr(retrieved, "bm25_dense_disagree", getattr(retriever, "last_bm25_dense_disagree", False))
    answer = generator.generate_answer(body, retrieved, lang=lang_for_retriever, bm25_dense_disagree=disagree)

    return {
        "reply": answer.answer_text,
        "language": active_lang,
        "citations": answer.citations,
        "confidence_flags": answer.confidence_flags,
        "sender_hash": session["sender_hash"]
    }


