from sentence_transformers import util
from backend.storage.models import Resume, JobDescription, MatchResult
from .embedder import embed_text


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