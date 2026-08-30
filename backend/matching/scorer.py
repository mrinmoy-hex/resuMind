from sentence_transformers import util

from backend.storage.models import (
    Resume,
    JobDescription,
    MatchResult,
)

from .embedder import embed_text
from .keyword_extractor import get_keyword_matches
from backend.matching.llm_reasoner import generate_analysis


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def calculate_experience_score(
    required: float | None,
    candidate: float | None,
) -> float:

    # No requirement means experience should not penalize
    # the candidate.
    if required is None:
        return 1.0

    # Requirement exists but resume doesn't provide evidence.
    if candidate is None:
        return 0.5

    if required <= 0:
        return 1.0

    return _clamp(candidate / required)


def rank_resumes(
    jd: JobDescription,
    resumes: list[Resume],
    keyword_count: int = 15,
) -> list[MatchResult]:

    if not resumes:
        return []

    # Whole-document semantic similarity remains useful,
    # but it is no longer the only signal.
    jd_embedding = embed_text(jd.raw_text)

    results = []

    requirements = jd.required_skills[:keyword_count]

    for resume in resumes:

        resume_embedding = embed_text(
            resume.raw_text
        )

        semantic_score = util.cos_sim(
            jd_embedding,
            resume_embedding,
        ).item()

        semantic_score = _clamp(
            semantic_score
        )

        matched, missing = get_keyword_matches(
            requirements,
            resume.raw_text,
        )

        if requirements:
            skill_score = (
                len(matched) / len(requirements)
            )
        else:
            skill_score = semantic_score

        experience_score = calculate_experience_score(
            jd.min_experience_years,
            resume.experience_years,
        )

        # Main scoring model.
        #
        # Skills matter most because this is a screening system.
        # Overall semantic similarity provides contextual matching.
        # Experience provides an explicit requirement signal.
        final_score = (
            0.55 * skill_score
            + 0.25 * semantic_score
            + 0.20 * experience_score
        )

        final_score = _clamp(
            final_score
        )

        results.append(
            MatchResult(
                resume=resume,
                score=final_score,
                semantic_score=semantic_score,
                skill_score=skill_score,
                experience_score=experience_score,
                matched_keywords=matched,
                missing_keywords=missing,
            )
        )

    return sorted(
        results,
        key=lambda result: result.score,
        reverse=True,
    )


def add_justifications(
    jd: JobDescription,
    ranked_results: list[MatchResult],
    top_n: int = 5,
    enabled: bool = True,
) -> list[MatchResult]:

    if not enabled:
        return ranked_results

    for result in ranked_results[:top_n]:

        analysis = generate_analysis(
            jd,
            result,
        )

        if not analysis:
            continue

        result.justification = analysis.get(
            "summary",
            "",
        )

        result.strengths = analysis.get(
            "strengths",
            [],
        )

        result.concerns = analysis.get(
            "concerns",
            [],
        )

    return ranked_results