from pathlib import Path
import pandas as pd
import pdfplumber
from docx import Document


# ---- Single-document parsers (PDF, DOCX, TXT) ----

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

def _guess_text_column(df: pd.DataFrame) -> str:
    """Picks the column most likely to hold resume/JD body text:
    the string-typed column with the longest average text length."""
    
    candidates = df.select_dtypes(include="object").columns
    if len(candidates) == 0:
        raise ValueError("No text-like columns found in this CSV.")
    
    avg_lengths = {col: df[col].astype(str).str.len().mean() for col in candidates}
    
    return max(avg_lengths, key=avg_lengths.get)


def load_texts_from_csv(csv_path: str, text_column: str | None = None) -> list[tuple[str, str]]:
    """
    Returns a list of (identifier, raw_text) tuples, one per row.
    text_column: exact column name to use. If None, auto-detects the most
    likely text column — useful for scripts; the Streamlit UI should still
    let the user pick explicitly via a dropdown.
    """
    df = pd.read_csv(csv_path)

    if text_column is None:
        text_column = _guess_text_column(df)

    if text_column not in df.columns:
        raise ValueError(
            f"Column '{text_column}' not found. Available columns: {list(df.columns)}"
        )

    results = []
    for idx, row in df.iterrows():
        identifier = f"{Path(csv_path).stem}_row_{idx}"
        results.append((identifier, str(row[text_column])))
    return results