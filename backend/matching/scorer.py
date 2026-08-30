from sentence_transformers import util
from backend.storage.models import Resume, JobDescription, MatchResult
from .embedder import embed_text
from matching.llm_reasoner import generate_justification


def rank_resumes(jd: JobDescription, resumes: list[Resume]) -> list[MatchResult]:
    jd_embedding = embed_text(jd.raw_text)
    results = []
    for resume in resumes:
        resume_embedding = embed_text(resume.raw_text)
        # cos_sim ranges roughly 0 (unreleadted) to 1 (near-identical meaning)
        score = util.cos_sim(jd_embedding, resume_embedding).item()
        results.append(MatchResult(resume=resume, score=score))
    
    # highes scoring (best-making ) candidate first
    return sorted(results, key=lambda r: r.score, reverse=True)

def add_justifications(jd, ranked_results, top_n: int = 5, enabled: bool = True):
    if not enabled:
        return ranked_results
    for result in ranked_results[:top_n]:
        result.justification = generate_justification(jd.raw_text, result.resume.raw_text)
    return ranked_results