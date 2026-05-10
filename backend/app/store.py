# Module-level variables to store the current document
current_filename = None
current_text = None

def clear():
    """
    Reset document store variables and clear the RAG index.
    """
    global current_filename, current_text
    current_filename = None
    current_text = None
    
    # Import rag and cache inside function to avoid circular imports
    from . import rag, cache
    rag.clear()
    cache.clear_cache()

def set_document(filename: str, text: str):
    """
    Saves the uploaded document details and clears previous state.
    """
    global current_filename, current_text
    clear()
    current_filename = filename
    current_text = text

def get_document():
    """
    Returns the currently stored document filename and text.
    """
    return current_filename, current_text
