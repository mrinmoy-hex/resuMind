from pathlib import Path

import pandas as pd
import pdfplumber
from docx import Document


def extract_text_from_pdf(
    file_path: str,
) -> str:

    text_chunks = []

    with pdfplumber.open(file_path) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                text_chunks.append(
                    page_text
                )

    return "\n".join(
        text_chunks
    ).strip()


def extract_text_from_docx(
    file_path: str,
) -> str:

    doc = Document(file_path)

    paragraphs = [
        paragraph.text.strip()
        for paragraph in doc.paragraphs
        if paragraph.text.strip()
    ]

    return "\n".join(
        paragraphs
    )


def extract_text_from_txt(
    file_path: str,
) -> str:

    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as file:

        return file.read().strip()


def extract_text(
    file_path: str,
) -> str:

    suffix = Path(
        file_path
    ).suffix.lower()

    if suffix == ".pdf":
        return extract_text_from_pdf(
            file_path
        )

    if suffix == ".docx":
        return extract_text_from_docx(
            file_path
        )

    if suffix == ".txt":
        return extract_text_from_txt(
            file_path
        )

    raise ValueError(
        f"Unsupported file type: {suffix}"
    )


def guess_text_column(
    df: pd.DataFrame,
) -> str:

    candidates = (
        df.select_dtypes(
            include="object"
        ).columns
    )

    if len(candidates) == 0:
        raise ValueError(
            "No text-like columns found in this CSV."
        )

    avg_lengths = {
        column: df[column]
        .fillna("")
        .astype(str)
        .str.len()
        .mean()
        for column in candidates
    }

    return max(
        avg_lengths,
        key=avg_lengths.get,
    )


def load_texts_from_csv(
    csv_path: str,
    text_column: str | None = None,
) -> list[tuple[str, str]]:

    df = pd.read_csv(csv_path)

    if df.empty:
        return []

    if text_column is None:
        text_column = guess_text_column(
            df
        )

    if text_column not in df.columns:
        raise ValueError(
            f"Column '{text_column}' not found. "
            f"Available columns: {list(df.columns)}"
        )

    results = []

    for idx, row in df.iterrows():

        text = str(
            row[text_column]
        ).strip()

        if not text:
            continue

        identifier = (
            f"{Path(csv_path).stem}"
            f"_row_{idx}"
        )

        results.append(
            (
                identifier,
                text,
            )
        )

    return results