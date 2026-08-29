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


@dataclass
class MatchResult:
    resume: Resume
    score: float
    justification: Optional[str] = None