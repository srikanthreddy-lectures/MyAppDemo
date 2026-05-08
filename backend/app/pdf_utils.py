from io import BytesIO
from pypdf import PdfReader

def extract_text_from_pdf(pdf_bytes: bytes) -> tuple[str, int]:
    """
    Extract text from uploaded PDFs using pypdf.
    
    Returns:
        tuple[str, int]: (full_text, page_count)
    
    Raises:
        ValueError: If no extractable text is found or if parsing fails.
    """
    try:
        pdf_file = BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        
        pages_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)
            else:
                pages_text.append("")
        
        full_text = "\n\n".join(pages_text).strip()
        page_count = len(reader.pages)
        
        if not full_text:
            raise ValueError("No extractable text found in this PDF.")
            
        return full_text, page_count
        
    except Exception as e:
        if isinstance(e, ValueError):
            raise e
        raise ValueError(f"Could not read PDF: {e}")
