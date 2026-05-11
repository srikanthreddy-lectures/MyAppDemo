from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import traceback

from . import store, rag, llm, classifier, agent
from .pdf_utils import extract_text_from_pdf
from .llm import GroqError

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="AskMyNotes", version="0.7.0")

# Enable CORS to allow Hugging Face's iframe and proxy to interact with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for deployment flexibility
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
    tool_used: str
    question_type: str
    used_chunks: list[str]

class UploadResponse(BaseModel):
    filename: str
    pages: int
    chars: int
    preview: str
    chunks_indexed: int

@app.get("/health")
def health_check():
    return {"ok": True}

@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=415, detail="Please upload a PDF.")
    
    try:
        pdf_bytes = await file.read()
        text, pages = extract_text_from_pdf(pdf_bytes)
        
        # Store in memory
        store.set_document(file.filename, text)
        
        # Index chunks for RAG
        rag.index_text(text)
        
        return UploadResponse(
            filename=file.filename,
            pages=pages,
            chars=len(text),
            preview=text[:200],
            chunks_indexed=rag.count()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    # STEP 1 — CLASSIFY FIRST
    try:
        question_type = classifier.classify(request.question)
    except Exception as e:
        print(f"Classification error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Classification failed: {e}")
    
    try:
        # STEP 2 — ROUTE TO TOOL
        tool, answer, chunks = await agent.route(request.question)
        
        # STEP 3 — RETURN RESPONSE
        return AskResponse(
            answer=answer,
            tool_used=tool,
            question_type=question_type,
            used_chunks=chunks
        )
    except GroqError:
        # Handle offline mode: return a polite message instead of a 502 error
        return AskResponse(
            answer="currently offline mode waiting for online mode",
            tool_used="offline",
            question_type=question_type,
            used_chunks=[]
        )
    except Exception as e:
        print(f"Unexpected error in /ask: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

# Mount StaticFiles LAST
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
