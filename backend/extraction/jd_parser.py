import re

from backend.storage.models import JobDescription
from backend.matching.keyword_extractor import extract_keywords


def extract_min_experience(text: str):
    """
    Extract the minimum requested experience from a JD.

    Examples:
        "3 years experience"
        "minimum 2 years"
        "2+ years of experience"
        "at least 5 years"
    """

    patterns = [
        r"(?:minimum|min\.?|at least)\s*(\d+(?:\.\d+)?)\s*\+?\s*years?",
        r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+(?:of\s+)?experience",
        r"experience\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\s*\+?\s*years?",
    ]

    matches = []

    for pattern in patterns:
        for match in re.finditer(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            matches.append(float(match.group(1)))

    if not matches:
        return None

    return max(matches)


def extract_education_requirements(text: str) -> list[str]:
    """
    Extract common education phrases.

    This is intentionally conservative.
    """

    patterns = [
        r"\b(?:bachelor'?s?|master'?s?|ph\.?d\.?|diploma)\b"
        r"[^.\n]{0,80}",
    ]

    results = []

    for pattern in patterns:
        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        for match in matches:
            cleaned = re.sub(
                r"\s+",
                " ",
                match,
            ).strip(" :-,")

            if cleaned and cleaned not in results:
                results.append(cleaned)

    return results[:5]


def build_job_description(
    file_path: str,
    raw_text: str,
    title: str = "Untitled Role",
    keyword_count: int = 15,
) -> JobDescription:

    if not raw_text or not raw_text.strip():
        raise ValueError(
            "Job description contains no readable text."
        )

    required_skills = extract_keywords(
        raw_text,
        top_n=keyword_count,
    )

    min_experience = extract_min_experience(
        raw_text,
    )

    education_requirements = (
        extract_education_requirements(raw_text)
    )

    return JobDescription(
        file_path=file_path,
        title=title,
        raw_text=raw_text,
        required_skills=required_skills,
        min_experience_years=min_experience,
        education_requirements=education_requirements,
    )