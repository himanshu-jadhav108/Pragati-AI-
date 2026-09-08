import io
from typing import Tuple

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from normal PDF using pypdfium2 with fallback to pdfminer."""
    # Attempt 1: pypdfium2
    try:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(file_bytes)
        text_parts = []
        for page in pdf:
            textpage = page.get_textpage()
            text_parts.append(textpage.get_text_range())
        extracted = "\n".join(text_parts).strip()
        if extracted:
            return extracted
    except Exception:
        pass

    # Attempt 2: pdfminer
    try:
        from pdfminer.high_level import extract_text
        extracted = extract_text(io.BytesIO(file_bytes)).strip()
        if extracted:
            return extracted
    except Exception:
        pass

    return ""

def parse_uploaded_document(filename: str, file_bytes: bytes) -> Tuple[str, str]:
    """Returns (file_type, extracted_text)"""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
        return "pdf", text
    elif lower.endswith(".txt") or lower.endswith(".dpr") or lower.endswith(".log"):
        text = file_bytes.decode("utf-8", errors="replace").strip()
        return "txt", text
    elif lower.endswith(".csv"):
        text = file_bytes.decode("utf-8", errors="replace").strip()
        return "csv", text
    else:
        # Generic text attempt
        text = file_bytes.decode("utf-8", errors="replace").strip()
        return "unknown", text
