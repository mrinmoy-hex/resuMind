from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Resume:
    file_path: str
    candidate_name: str
    raw_text: str

    skills: list[str] = field(default_factory=list)
    experience_years: Optional[float] = None
    education: list[str] = field(default_factory=list)


@dataclass
class JobDescription:
    file_path: str
    title: str
    raw_text: str

    required_skills: list[str] = field(default_factory=list)
    min_experience_years: Optional[float] = None
    education_requirements: list[str] = field(default_factory=list)


@dataclass
class MatchResult:
    resume: Resume

    # Final weighted score
    score: float

    # Component scores
    semantic_score: float = 0.0
    skill_score: float = 0.0
    experience_score: float = 0.0

    # Requirement-level information
    matched_keywords: list[str] = field(default_factory=list)
    missing_keywords: list[str] = field(default_factory=list)

    # LLM-generated explanation
    justification: Optional[str] = None
    strengths: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)