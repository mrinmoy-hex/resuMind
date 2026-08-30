import re
from pathlib import Path

from backend.storage.models import Resume
from backend.matching.keyword_extractor import extract_keywords


EDUCATION_TERMS = (
    "b.tech",
    "b.e",
    "bachelor",
    "b.sc",
    "bca",
    "m.tech",
    "m.e",
    "master",
    "m.sc",
    "mca",
    "ph.d",
    "phd",
    "diploma",
)


def build_resume(
    file_path: str,
    raw_text: str,
    display_name: str | None = None,
) -> Resume:

    if not raw_text or not raw_text.strip():
        raise ValueError(
            "Resume contains no readable text."
        )

    candidate_name = _guess_name(
        raw_text,
        display_name or file_path,
    )

    skills = extract_keywords(
        raw_text,
        top_n=20,
    )

    experience_years = _extract_experience(
        raw_text,
    )

    education = _extract_education(
        raw_text,
    )

    return Resume(
        file_path=file_path,
        candidate_name=candidate_name,
        raw_text=raw_text,
        skills=skills,
        experience_years=experience_years,
        education=education,
    )


def _guess_name(
    raw_text: str,
    source_name: str,
) -> str:

    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in raw_text.splitlines()
    ]

    # Ignore common resume headings.
    ignored = {
        "resume",
        "curriculum vitae",
        "cv",
        "profile",
        "professional resume",
    }

    candidates = []

    for line in lines[:15]:

        if not line:
            continue

        lower = line.lower()

        if lower in ignored:
            continue

        if len(line.split()) > 5:
            continue

        if len(line) < 3 or len(line) > 60:
            continue

        if re.search(r"\d", line):
            continue

        if "@" in line or "http" in lower:
            continue

        if any(
            symbol in line
            for symbol in ["|", ":", "/", "\\"]
        ):
            continue

        candidates.append(line)

    if candidates:
        return candidates[0]

    # Better fallback than the temporary filename.
    stem = Path(source_name).stem

    stem = re.sub(
        r"[_\-]+",
        " ",
        stem,
    )

    stem = re.sub(
        r"\b(resume|cv|curriculum vitae)\b",
        "",
        stem,
        flags=re.IGNORECASE,
    )

    stem = re.sub(
        r"\s+",
        " ",
        stem,
    ).strip()

    return stem.title() or "Unnamed Candidate"


def _extract_experience(text: str):
    """
    Estimate years of experience from explicit resume statements.

    Examples:
        "4 years of experience"
        "3+ years experience"
        "5 years in software development"
    """

    patterns = [
        r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+(?:of\s+)?experience",
        r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+in\s+",
    ]

    values = []

    for pattern in patterns:
        for match in re.finditer(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            values.append(
                float(match.group(1))
            )

    if not values:
        return None

    return max(values)


def _extract_education(text: str) -> list[str]:

    results = []

    for line in text.splitlines():

        cleaned = re.sub(
            r"\s+",
            " ",
            line,
        ).strip()

        if not cleaned:
            continue

        lower = cleaned.lower()

        if any(
            term in lower
            for term in EDUCATION_TERMS
        ):
            if cleaned not in results:
                results.append(cleaned)

    return results[:8]