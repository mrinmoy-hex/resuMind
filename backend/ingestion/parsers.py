from pathlib import Path
import pandas as pd
import pdfplumber
from docx import Document


# ---- Single-document parsers (PDF, DOCX, TXT) ----
# Each of these takes one file and returns one string of raw text.

def extract_text_from_pdf(file_path: str) -> str:
    text_chunks = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_chunks.append(page_text)
    return "\n".join(text_chunks)


def extract_text_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    return "\n".join(para.text for para in doc.paragraphs if para.text.strip())


def extract_text_from_txt(file_path: str) -> str:
    # encoding="utf-8" avoids crashes on files with non-ASCII characters (names, accents, etc.)
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def extract_text(file_path: str) -> str:
    """Dispatcher for single-document files. Raises on unsupported types."""
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    elif suffix == ".docx":
        return extract_text_from_docx(file_path)
    elif suffix == ".txt":
        return extract_text_from_txt(file_path)
    raise ValueError(f"Unsupported file type: {suffix}")


# ---- Bulk parser (CSV) ----
# Returns a LIST of (identifier, raw_text) tuples — one per row — not a single string,
# since one CSV file can contain hundreds of resumes.

def load_texts_from_csv(csv_path: str, text_column: str) -> list[tuple[str, str]]:
    """
    text_column: the exact column name in your CSV holding resume text
                 (check this yourself with df.columns or `head file.csv` first)
    """
    df = pd.read_csv(csv_path)
    results = []
    for idx, row in df.iterrows():
        identifier = f"{Path(csv_path).stem}_row_{idx}"
        results.append((identifier, row[text_column]))
    return results