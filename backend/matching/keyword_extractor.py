import re

from keybert import KeyBERT
from sentence_transformers import util

from backend.matching.embedder import get_model, embed_text, embed_texts

# Cache the KeyBERT model to avoid reloading it on every re-run of the Streamlit app
_kw_model = None


def get_keyword_model() -> KeyBERT:
    global _kw_model

    if _kw_model is None:
        _kw_model = KeyBERT(model=get_model())

    return _kw_model


def extract_keywords(
    text: str,
    top_n: int = 15,
) -> list[str]:
    """
    Extract important phrases from a document using KeyBERT.
    """

    if not text or not text.strip():
        return []

    keywords = get_keyword_model().extract_keywords(
        text,
        keyphrase_ngram_range=(1, 2),
        stop_words="english",
        top_n=top_n,
        use_mmr=True,
        diversity=0.5,
    )

    return [
        phrase.strip()
        for phrase, _score in keywords
        if phrase.strip()
    ]


def _split_resume_into_chunks(text: str) -> list[str]:
    """
    Split resume text into reasonably meaningful pieces.

    Matching a requirement against individual resume chunks is
    much more useful than comparing the requirement against the
    entire resume as one vector.
    """

    chunks = re.split(
        r"\n+|(?<=[.!?])\s+",
        text,
    )

    cleaned = []

    for chunk in chunks:
        chunk = re.sub(r"\s+", " ", chunk).strip()

        if len(chunk) >= 10:
            cleaned.append(chunk)

    return cleaned


def find_matched_keywords(
    jd_text: str,
    resume_text: str,
    top_n: int = 15,
    threshold: float = 0.55,
) -> list[str]:
    """
    Find JD requirements that are either:

    1. Explicitly present in the resume, or
    2. Semantically similar to something in the resume.
    """

    jd_keywords = extract_keywords(
        jd_text,
        top_n=top_n,
    )

    if not jd_keywords:
        return []

    resume_lower = resume_text.lower()

    # Fast exact matching first.
    exact_matches = [
        keyword
        for keyword in jd_keywords
        if keyword.lower() in resume_lower
    ]

    remaining = [
        keyword
        for keyword in jd_keywords
        if keyword not in exact_matches
    ]

    if not remaining:
        return exact_matches

    chunks = _split_resume_into_chunks(resume_text)

    if not chunks:
        return exact_matches

    requirement_embeddings = embed_texts(remaining)
    chunk_embeddings = embed_texts(chunks)

    similarities = util.cos_sim(
        requirement_embeddings,
        chunk_embeddings,
    )

    semantic_matches = []

    for i, keyword in enumerate(remaining):
        best_score = similarities[i].max().item()

        if best_score >= threshold:
            semantic_matches.append(keyword)

    return exact_matches + semantic_matches


def get_keyword_matches(
    requirements: list[str],
    resume_text: str,
    threshold: float = 0.55,
) -> tuple[list[str], list[str]]:
    """
    Compare individual requirements against the resume.

    Returns:
        matched_requirements
        missing_requirements
    """

    if not requirements:
        return [], []

    chunks = _split_resume_into_chunks(resume_text)

    if not chunks:
        return [], requirements.copy()

    resume_lower = resume_text.lower()

    remaining = []
    matched = []

    # Exact matches
    for requirement in requirements:
        if requirement.lower() in resume_lower:
            matched.append(requirement)
        else:
            remaining.append(requirement)

    if not remaining:
        return matched, []

    requirement_embeddings = embed_texts(remaining)
    chunk_embeddings = embed_texts(chunks)

    similarities = util.cos_sim(
        requirement_embeddings,
        chunk_embeddings,
    )

    for i, requirement in enumerate(remaining):

        best_score = similarities[i].max().item()

        if best_score >= threshold:
            matched.append(requirement)

    missing = [
        requirement
        for requirement in requirements
        if requirement not in matched
    ]

    return matched, missing