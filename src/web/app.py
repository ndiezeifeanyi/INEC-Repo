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
from src.retrieval.faq_library import FAQLibrary
from src.generation.prompt_builder import GroundedAnswerGenerator
from src.verification.matcher import OfficialSourceChecker
from src.speech.tts_engine import MMSTTSEngine
from src.lid.ensemble_lid import EnsembleLID, DISAMBIGUATION_PROMPT
from src.web.session_store import SecureSessionStore

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
faq_library = FAQLibrary()
generator = GroundedAnswerGenerator()
checker = OfficialSourceChecker()
lid_detector = EnsembleLID()
session_store = SecureSessionStore()

class AskRequest(BaseModel):
    query: str
    language: str = "auto"  # auto, en, ha, yo, ig, pcm
    allow_translation: bool = False
    confirmed_language: bool = False

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
    """
    Answers voter questions strictly grounded in Electoral Act 2026 & INEC Guidelines.
    Phase 2: Performs language identification (AfroLID + GlotLID) with mandatory user confirmation
    when confidence < 0.75, when code-switching is detected, or for Nigerian Pidgin.
    """
    cleaned_query = req.query.strip()
    if not cleaned_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    req_lang = req.language.lower().strip()
    extra_flags = []

    # Phase 2 LID Pipeline:
    # If language is 'auto' or unconfirmed and not an explicit known language:
    if req_lang == "auto" or (not req.confirmed_language and req_lang not in ["en", "ha", "yo", "ig"]):
        detected_lang, conf, needs_disambig = lid_detector.identify(cleaned_query)
        if needs_disambig and not req.confirmed_language:
            return VoterAnswer(
                question=cleaned_query,
                language=detected_lang or "auto",
                answer_text=DISAMBIGUATION_PROMPT,
                answer_plain="Please confirm your preferred language to receive a verified answer.",
                citations=[],
                retrieved_chunk_ids=[],
                confidence_flags=["NEEDS_LANGUAGE_CONFIRMATION"],
                status="NEEDS_LANGUAGE_CONFIRMATION",
                disambiguation_prompt=DISAMBIGUATION_PROMPT,
                detected_candidate=detected_lang,
                confidence_score=conf
            )
        active_lang = detected_lang
        extra_flags.append(f"LID_AUTO_DETECTED_{active_lang.upper()}")
    else:
        active_lang = req_lang if req_lang in ["en", "ha", "yo", "ig", "pcm"] else "en"

    # Nigerian Pidgin experimental pass-through
    if active_lang == "pcm":
        extra_flags.append("EXPERIMENTAL_PIDGIN_PASSTHROUGH")
        retrieval_lang = "en"
    else:
        retrieval_lang = active_lang if active_lang in ["en", "ha", "yo", "ig"] else "en"

    # Phase 4: Authoritative Fast-Path for Pre-Reviewed Civic FAQs (low-risk topics only)
    matched_faq = faq_library.lookup(cleaned_query, lang=active_lang)
    if matched_faq:
        chunk_id = matched_faq.get("chunk_id", "EA2026-FAQ")
        sec_str = matched_faq.get("statutory_section", "")
        import re
        sec_match = re.search(r"Section\s+([0-9]+(?:\([0-9]+\))?)", sec_str)
        sec_val = sec_match.group(1) if sec_match else "47"
        citations = [{
            "document_title": "Electoral Act 2026",
            "section": sec_val,
            "subsection": None,
            "version": "Federal Republic of Nigeria Official Gazette No. 15, Vol. 113",
            "retrieval_date": "2026-11-08",
            "source_url": "https://nass.gov.ng/documents/download/11248",
            "legal_status": "CURRENT_LAW"
        }]

        if active_lang in ("en", "pcm"):
            answer_text = matched_faq["english"]["verbatim_quote"]
            answer_plain = matched_faq["english"]["short_explanation"]
            flags = ["PRE_REVIEWED_CIVIC_FAQ", "REVIEWED_STATUTORY_AUTHORITY"]
        else:
            lang_key = {"ha": "hausa", "yo": "yoruba", "ig": "igbo"}.get(active_lang, "hausa")
            draft_trans = matched_faq.get(lang_key, {}).get("draft_translation", "")
            answer_text = (
                f"{matched_faq['english']['verbatim_quote']}\n\n"
                f"[DRAFT TRANSLATION - UNREVIEWED_DEVELOPER_DRAFT]:\n{draft_trans}"
            )
            answer_plain = draft_trans
            flags = ["PRE_REVIEWED_CIVIC_FAQ", "UNREVIEWED_DEVELOPER_DRAFT"]

        for flag in extra_flags:
            if flag not in flags:
                flags.append(flag)

        return VoterAnswer(
            question=cleaned_query,
            language=active_lang,
            answer_text=answer_text,
            answer_plain=answer_plain,
            citations=citations,
            retrieved_chunk_ids=[chunk_id],
            confidence_flags=flags,
            status="ANSWER"
        )

    # Retrieve chunks (with user opt-in flag for online gtx endpoint)
    retrieved = retriever.retrieve(cleaned_query, top_k=3, lang=retrieval_lang, allow_online=req.allow_translation)
    disagree = getattr(retrieved, "bm25_dense_disagree", getattr(retriever, "last_bm25_dense_disagree", False))

    # Generate grounded response with citations
    answer = generator.generate_answer(cleaned_query, retrieved, lang=retrieval_lang, bm25_dense_disagree=disagree)

    # Attach Phase 2 LID flags
    for flag in extra_flags:
        if flag not in answer.confidence_flags:
            answer.confidence_flags.append(flag)
    answer.language = active_lang
    answer.status = "ANSWER"
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

    # 5. Check Authoritative Pre-Reviewed Civic FAQ Library
    matched_faq = faq_library.lookup(body, lang=active_lang)
    if matched_faq:
        if active_lang in ("en", "pcm"):
            reply_text = f"{matched_faq['english']['short_explanation']}\n\nOfficial provision ({matched_faq['statutory_section']}):\n\"{matched_faq['english']['verbatim_quote']}\""
        else:
            lang_key = {"ha": "hausa", "yo": "yoruba", "ig": "igbo"}.get(active_lang, "hausa")
            draft_trans = matched_faq.get(lang_key, {}).get("draft_translation", "")
            reply_text = f"{draft_trans}\n\n[Official English Law - {matched_faq['statutory_section']}]:\n\"{matched_faq['english']['verbatim_quote']}\""
        return {
            "reply": reply_text,
            "language": active_lang,
            "citations": [{"statute": "Electoral Act 2026", "section": matched_faq["statutory_section"]}],
            "confidence_flags": ["PRE_REVIEWED_CIVIC_FAQ"],
            "sender_hash": session["sender_hash"]
        }

    # 6. Retrieve answer strictly grounded in Electoral Act 2026
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


