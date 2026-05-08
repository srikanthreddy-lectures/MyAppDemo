import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 512
DEFAULT_TIMEOUT_SECONDS = 15.0

class GroqError(Exception):
    """Custom exception for Groq API errors."""
    pass

async def generate(prompt: str, system_prompt: str = "You are a helpful assistant."):
    """
    Connect to Groq chat completions API using raw HTTP requests.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise GroqError("GROQ_API_KEY is missing from environment variables.")
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": DEFAULT_TEMPERATURE,
        "max_tokens": DEFAULT_MAX_TOKENS
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS) as client:
            response = await client.post(
                GROQ_API_URL,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            
            return data["choices"][0]["message"]["content"]
            
    except httpx.HTTPStatusError as e:
        raise GroqError(f"Groq API returned error: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        raise GroqError(f"Network error occurred while connecting to Groq: {e}")
    except (KeyError, IndexError) as e:
        raise GroqError(f"Malformed response received from Groq: {e}")
    except Exception as e:
        raise GroqError(f"An unexpected error occurred: {e}")
