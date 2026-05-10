import sqlite3
import json
import os

DB_PATH = "askmynotes_cache.db"

def init_db():
    """Initialize the SQLite database and create the cache table."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS query_cache (
                query TEXT PRIMARY KEY,
                tool TEXT,
                answer TEXT,
                chunks TEXT
            )
        """)
        conn.commit()

# Initialize DB on module load
init_db()

def get_cached_response(query: str):
    """Retrieve a cached response for a given query."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT tool, answer, chunks FROM query_cache WHERE query = ?", 
            (query,)
        )
        row = cursor.fetchone()
        if row:
            tool, answer, chunks_json = row
            return tool, answer, json.loads(chunks_json)
    return None

def set_cached_response(query: str, tool: str, answer: str, chunks: list):
    """Store a response in the cache."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO query_cache (query, tool, answer, chunks) VALUES (?, ?, ?, ?)",
            (query, tool, answer, json.dumps(chunks))
        )
        conn.commit()

def clear_cache():
    """Clear all cached queries. Useful when a new document is uploaded."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM query_cache")
        conn.commit()
