import httpx

CLASSIFIER_URL = "https://scott2srikanth-askmynotes-classifier.hf.space/predict"
DEFAULT_TIMEOUT_SECONDS = 10.0
VALID_LABELS = (
    "summary",
    "action item",
    "timeline",
    "synthesis",
    "flashcard",
    "definition",
    "example",
    "comparison",
)
FALLBACK_LABEL = "definition"

def classify(question: str) -> str:
    if not question or not question.strip():
        return FALLBACK_LABEL

    try:
        payload = {"question": question}
        with httpx.Client(timeout=DEFAULT_TIMEOUT_SECONDS) as client:
            response = client.post(CLASSIFIER_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Try 'label' first (as per spec), then 'predicted_category' (as per observed behavior)
            label = data.get("label") or data.get("predicted_category", "")
            
            if isinstance(label, str):
                normalized_label = label.lower().strip()
                if normalized_label in VALID_LABELS:
                    return normalized_label
                    
    except Exception:
        pass

    return FALLBACK_LABEL
