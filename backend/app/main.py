from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="AskMyNotes", version="0.1.0")

# Module-level state
current_filename: str | None = None

# Pydantic Models
class AskRequest(BaseModel):
    question: str

class UploadResponse(BaseModel):
    filename: str
    size_bytes: int
    received: bool

class Pill(BaseModel):
    label: str
    value: str

class AskResponse(BaseModel):
    answer: str
    tool_used: str
    question_type: str
    used_chunks: list[str]

@app.get("/health")
def health_check():
    return {"ok": True}

@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=415, detail="Please upload a PDF.")
    
    data = await file.read()
    size_bytes = len(data)
    
    global current_filename
    current_filename = file.filename
    
    return UploadResponse(
        filename=file.filename,
        size_bytes=size_bytes,
        received=True
    )

@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    global current_filename
    
    if current_filename is None:
        return AskResponse(
            answer="No notes uploaded yet. Upload a PDF first.",
            tool_used="search_notes",
            question_type="definition",
            used_chunks=[]
        )
    
    question = request.question.lower()
    
    # Logic for tool_used
    if any(char.isdigit() for char in question) or any(op in question for op in ['+', '-', '*', '/', '=']):
        tool_used = "calculator"
        used_chunks = []
    else:
        tool_used = "search_notes"
        used_chunks = [
            f"Chunk 1 from {current_filename}",
            f"Chunk 2 from {current_filename}",
            f"Chunk 3 from {current_filename}"
        ]
    
    # Logic for question_type
    if "compare" in question:
        question_type = "comparison"
    elif "example" in question:
        question_type = "example"
    else:
        question_type = "definition"
        
    return AskResponse(
        answer=f"Stub answer for: {request.question}",
        tool_used=tool_used,
        question_type=question_type,
        used_chunks=used_chunks
    )

# Mount static files AFTER all endpoints
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
