import json
import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


MODEL_NAME = "openai/gpt-oss-20b"


def _get_client():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return None

    return Groq(
        api_key=api_key,
    )


def generate_analysis(
    jd,
    result,
) -> dict | None:

    client = _get_client()

    if client is None:
        print(
            "GROQ_API_KEY is not configured."
        )
        return None

    resume = result.resume

    matched = ", ".join(
        result.matched_keywords
    ) or "None identified"

    missing = ", ".join(
        result.missing_keywords
    ) or "None identified"

    candidate_experience = (
        f"{resume.experience_years:g} years"
        if resume.experience_years is not None
        else "Not stated"
    )

    required_experience = (
        f"{jd.min_experience_years:g} years"
        if jd.min_experience_years is not None
        else "Not specified"
    )

    prompt = f"""
You are an AI assistant helping a recruiter screen a candidate.

Your job is to explain the evidence already found by the matching
system. Do not invent experience, skills, education, employers,
projects, or qualifications that are not present in the resume.

JOB TITLE:
{jd.title}

REQUIRED SKILLS:
{", ".join(jd.required_skills) or "Not extracted"}

REQUIRED EXPERIENCE:
{required_experience}

MATCHED REQUIREMENTS:
{matched}

MISSING OR WEAK REQUIREMENTS:
{missing}

CALCULATED SCORES:
Overall: {result.score:.0%}
Skill match: {result.skill_score:.0%}
Semantic match: {result.semantic_score:.0%}
Experience match: {result.experience_score:.0%}

CANDIDATE EXPERIENCE:
{candidate_experience}

RESUME:
{resume.raw_text[:6000]}

Return ONLY valid JSON with this structure:

{{
    "summary": "2 concise sentences explaining the overall match.",
    "strengths": [
        "specific strength supported by the resume"
    ],
    "concerns": [
        "specific missing or weak requirement"
    ]
}}

Keep each strength and concern short.
"""

    try:

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a careful recruitment analysis "
                        "assistant. Only use evidence from the "
                        "provided information."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            response_format={
                "type": "json_object",
            },
            temperature=0.1,
            max_tokens=500,
        )

        content = (
            response.choices[0]
            .message
            .content
        )

        if not content:
            return None

        data = json.loads(content)

        return {
            "summary": str(
                data.get("summary", "")
            ).strip(),

            "strengths": [
                str(item).strip()
                for item in data.get(
                    "strengths",
                    [],
                )
                if str(item).strip()
            ],

            "concerns": [
                str(item).strip()
                for item in data.get(
                    "concerns",
                    [],
                )
                if str(item).strip()
            ],
        }

    except Exception as exc:

        print(
            f"LLM analysis failed: {exc}"
        )

        return None


def generate_justification(
    jd_text: str,
    resume_text: str,
) -> str:

    """
    Backwards-compatible helper.

    If other code still calls generate_justification(),
    it won't break.
    """

    class TemporaryResume:
        def __init__(self, text):
            self.raw_text = text
            self.experience_years = None

    class TemporaryResult:
        def __init__(self, resume):
            self.resume = resume
            self.score = 0.0
            self.skill_score = 0.0
            self.semantic_score = 0.0
            self.experience_score = 0.0
            self.matched_keywords = []
            self.missing_keywords = []

    class TemporaryJD:
        def __init__(self, text):
            self.raw_text = text
            self.title = "Job"
            self.required_skills = []
            self.min_experience_years = None

    result = TemporaryResult(
        TemporaryResume(resume_text)
    )

    analysis = generate_analysis(
        TemporaryJD(jd_text),
        result,
    )

    if not analysis:
        return ""

    return analysis.get(
        "summary",
        "",
    )