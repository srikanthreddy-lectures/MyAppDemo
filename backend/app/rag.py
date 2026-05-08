import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Module state
_model = None
_chunks = []
_embeddings = None

def get_model():
    """
    Lazy-load the SentenceTransformer model.
    """
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def chunk_text(text: str):
    """
    Split text into overlapping chunks.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start += (CHUNK_SIZE - CHUNK_OVERLAP)
    return chunks

def index_text(text: str):
    """
    Chunk text, generate embeddings, and store them.
    """
    global _chunks, _embeddings
    
    chunks = chunk_text(text)
    model = get_model()
    
    # Generate embeddings
    embeddings = model.encode(chunks)
    
    # Normalize embeddings for cosine similarity
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized_embeddings = embeddings / norms
    
    _chunks = chunks
    _embeddings = np.array(normalized_embeddings)

def search(query: str, k=3):
    """
    Search for the top-k most relevant chunks using cosine similarity.
    """
    global _embeddings, _chunks
    if _embeddings is None or not _chunks:
        return []
        
    model = get_model()
    query_vector = model.encode([query])[0]
    
    # Normalize query vector
    query_norm = np.linalg.norm(query_vector)
    query_vector = query_vector / query_norm
    
    # Compute cosine similarity (dot product of normalized vectors)
    similarities = _embeddings @ query_vector
    
    # Get top-k indices
    top_indices = np.argsort(similarities)[::-1][:k]
    
    results = []
    for idx in top_indices:
        results.append({
            "text": _chunks[idx],
            "score": float(similarities[idx])
        })
        
    return results

def clear():
    """
    Clear chunks and embeddings.
    """
    global _chunks, _embeddings
    _chunks = []
    _embeddings = None

def count():
    """
    Return the number of indexed chunks.
    """
    return len(_chunks)
