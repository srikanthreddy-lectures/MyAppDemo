from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import store, rag, llm
from .pdf_utils import extract_text_from_pdf
from .llm import GroqError

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="AskMyNotes", version="0.5.0")

SYSTEM_PROMPT = """Answer ONLY from provided context.
Do not hallucinate.
Do not speculate.
Combine related facts.
Keep answers concise.
If answer missing: "The notes don't cover that."
"""

# Pydantic Models
class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
    tool_used: str
    question_type: str
    used_chunks: list[dict]  # List of {text, score}

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
    filename, text = store.get_document()
    
    if not text:
        return AskResponse(
            answer="No notes uploaded yet. Upload a PDF first.",
            tool_used="search_notes",
            question_type="definition",
            used_chunks=[]
        )
    
    try:
        # 1. Retrieve top-3 chunks
        chunks = rag.search(request.question, k=3)
        
        # 2. Build context prompt
        context = "\n\n".join([c["text"] for c in chunks])
        prompt = f"Context:\n{context}\n\nQuestion: {request.question}"
        
        # 3. Call LLM
        answer = await llm.generate(prompt, system_prompt=SYSTEM_PROMPT)
        
        return AskResponse(
            answer=answer,
            tool_used="search_notes",
            question_type="definition",
            used_chunks=chunks
        )
    except GroqError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

# Mount StaticFiles LAST
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
