from pathlib import Path
from .pdf_parser import extract_text_from_pdf
from .docx_parser import extract_text_from_docx


def extract_text(file_path: str) -> str:
    suffix = Path(file_path).suffix.lower()
    try:
        if suffix == ".pdf":
            return extract_text_from_pdf(file_path)
        elif suffix == ".docx":
            return extract_text_from_docx(file_path)
    
    # need to implement better logging 
    except ValueError:
        print(f"Unsupported file type: {suffix}")