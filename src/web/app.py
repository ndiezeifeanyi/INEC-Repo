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

class CheckRequest(BaseModel):
    item: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/v1/ask", response_model=VoterAnswer)
async def ask_election_rule(req: AskRequest):
    """Answers voter questions strictly grounded in Electoral Act 2026 & INEC Guidelines."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    lang = req.language.lower()
    if lang not in ["en", "ha", "yo", "ig"]:
        lang = "en"

    # Retrieve chunks
    retrieved = retriever.retrieve(req.query, top_k=3, lang=lang)

    # Generate grounded response with citations
    answer = generator.generate_answer(req.query, retrieved, lang=lang)
    return answer

@app.post("/api/v1/check", response_model=VerificationResult)
async def check_link_or_message(req: CheckRequest):
    """Verifies whether a link or message matches official published INEC records."""
    if not req.item.strip():
        raise HTTPException(status_code=400, detail="Item cannot be empty.")
    
    result = checker.verify(req.item)
    return result

@app.get("/api/v1/tts")
async def generate_speech(text: str, lang: str = "en"):
    """Synthesizes speech using Meta MMS-TTS under CC-BY-NC-4.0 license."""
    audio_bytes = MMSTTSEngine.generate_synthetic_audio(text, lang)
    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={
            "X-License": "CC-BY-NC-4.0 (Non-commercial research)",
            "Cache-Control": "public, max-age=86400"
        }
    )

@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "HEALTHY",
        "statutes": ["Electoral Act 2026", "INEC Guidelines 2026"],
        "section_29a_status": "PASSED_BILL_AWAITING_GAZETTE",
        "supported_languages": ["en", "ha", "yo", "ig"],
        "pidgin_status": "DISABLED_PENDING_VALIDATION",
        "live_inec_access": False,
        "pii_logging": False
    }
