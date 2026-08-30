import os
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from backend.ingestion import (
    extract_text,
    load_texts_from_csv,
    guess_text_column,
)

from backend.extraction.jd_parser import (
    build_job_description,
)

from backend.extraction.structurer import (
    build_resume,
)

from backend.matching.scorer import (
    rank_resumes,
    add_justifications,
)


# ============================================================
# Configuration
# ============================================================

load_dotenv()

st.set_page_config(
    page_title="ResuMind",
    page_icon="🧠",
    layout="wide",
)


# ============================================================
# Helpers
# ============================================================

def get_rating(
    score: float,
) -> tuple[str, str]:

    if score >= 0.75:
        return "Excellent Match", "🟢"

    if score >= 0.60:
        return "Strong Match", "🔵"

    if score >= 0.45:
        return "Moderate Match", "🟠"

    if score >= 0.30:
        return "Weak Match", "🔴"

    return "Poor Match", "⚪"


def save_to_temp(
    uploaded_file,
) -> str:

    suffix = Path(
        uploaded_file.name
    ).suffix

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    ) as tmp:

        tmp.write(
            uploaded_file.getbuffer()
        )

        return tmp.name


def safe_get(
    obj,
    attribute: str,
    default=None,
):
    return getattr(
        obj,
        attribute,
        default,
    )


def pick_text_column(
    df: pd.DataFrame,
    label: str,
    key: str,
) -> str:

    guessed_col = guess_text_column(
        df
    )

    if guessed_col not in df.columns:
        guessed_col = df.columns[0]

    index = df.columns.tolist().index(
        guessed_col
    )

    with st.expander(
        f"⚙️ Advanced: {label}",
        expanded=False,
    ):

        column = st.selectbox(
            "Text column",
            df.columns.tolist(),
            index=index,
            key=key,
        )

        if not df.empty:

            preview = str(
                df[column].iloc[0]
            )

            st.caption(
                "Preview: "
                + preview[:250]
                + (
                    "..."
                    if len(preview) > 250
                    else ""
                )
            )

    return column


def render_skill_list(
    title: str,
    skills: list[str],
):

    if not skills:
        return

    st.markdown(
        f"**{title}**"
    )

    st.write(
        " ".join(
            f"`{skill}`"
            for skill in skills
        )
    )


def render_candidate(
    rank: int,
    result,
):

    resume = result.resume

    score = float(
        safe_get(
            result,
            "score",
            0.0,
        )
    )

    label, icon = get_rating(
        score
    )

    with st.container(
        border=True
    ):

        header = st.columns(
            [0.6, 3.5, 2, 1.2]
        )

        with header[0]:
            st.markdown(
                f"## #{rank}"
            )

        with header[1]:
            st.markdown(
                f"### {resume.candidate_name}"
            )

            st.caption(
                resume.file_path
            )

        with header[2]:
            st.markdown(
                f"### {icon} {label}"
            )

        with header[3]:
            st.metric(
                "Match",
                f"{score:.0%}",
            )

        st.progress(
            max(
                0.0,
                min(
                    score,
                    1.0,
                ),
            )
        )

        # ----------------------------------------------------
        # Score breakdown
        # ----------------------------------------------------

        st.markdown(
            "#### 📊 Score Breakdown"
        )

        score_cols = st.columns(3)

        with score_cols[0]:
            st.metric(
                "Skills",
                f"{result.skill_score:.0%}",
            )

        with score_cols[1]:
            st.metric(
                "Semantic",
                f"{result.semantic_score:.0%}",
            )

        with score_cols[2]:
            st.metric(
                "Experience",
                f"{result.experience_score:.0%}",
            )

        # ----------------------------------------------------
        # Requirements
        # ----------------------------------------------------

        matched = safe_get(
            result,
            "matched_keywords",
            [],
        )

        missing = safe_get(
            result,
            "missing_keywords",
            [],
        )

        if matched:

            st.markdown(
                "#### ✅ Matched Requirements"
            )

            st.write(
                " ".join(
                    f"`{item}`"
                    for item in matched
                )
            )

        if missing:

            st.markdown(
                "#### ⚠️ Missing / Weak Requirements"
            )

            st.write(
                " ".join(
                    f"`{item}`"
                    for item in missing
                )
            )

        # ----------------------------------------------------
        # Experience
        # ----------------------------------------------------

        experience = resume.experience_years

        if experience is not None:

            st.caption(
                f"Detected experience: "
                f"{experience:g} years"
            )

        # ----------------------------------------------------
        # LLM analysis
        # ----------------------------------------------------

        justification = safe_get(
            result,
            "justification",
            None,
        )

        strengths = safe_get(
            result,
            "strengths",
            [],
        )

        concerns = safe_get(
            result,
            "concerns",
            [],
        )

        if justification:

            st.markdown(
                "#### 🤖 AI Analysis"
            )

            st.info(
                justification
            )

            analysis_cols = st.columns(
                2
            )

            with analysis_cols[0]:

                if strengths:

                    st.markdown(
                        "**Strengths**"
                    )

                    for strength in strengths:
                        st.markdown(
                            f"✓ {strength}"
                        )

            with analysis_cols[1]:

                if concerns:

                    st.markdown(
                        "**Concerns**"
                    )

                    for concern in concerns:
                        st.markdown(
                            f"⚠ {concern}"
                        )


# ============================================================
# Sidebar
# ============================================================

with st.sidebar:

    st.title("🧠 ResuMind")

    st.caption(
        "AI-assisted resume screening "
        "and candidate ranking."
    )

    st.divider()

    st.subheader(
        "⚙️ Settings"
    )

    enable_llm = st.toggle(
        "Generate AI analysis",
        value=True,
    )

    top_n = st.slider(
        "Analyze top candidates",
        min_value=1,
        max_value=10,
        value=5,
        disabled=not enable_llm,
    )

    keyword_count = st.slider(
        "JD requirements",
        min_value=5,
        max_value=25,
        value=15,
    )

    st.divider()

    st.markdown(
        """
### How ResuMind works

**1. Extract**  
Read the JD and resumes.

**2. Understand**  
Generate semantic embeddings.

**3. Match**  
Compare job requirements
against candidate evidence.

**4. Rank**  
Calculate a weighted score.

**5. Explain**  
Use an LLM to explain
the result.
"""
    )

    st.divider()

    st.caption(
        "Built by Mrinmoy"
    )

    st.markdown(
        "[GitHub](https://github.com/mrinmoy-hex)"
    )


# ============================================================
# Header
# ============================================================

st.title(
    "🧠 ResuMind"
)

st.write(
    "AI-powered resume screening that "
    "matches candidates against job "
    "requirements and explains the ranking."
)

st.divider()


# ============================================================
# Job Description
# ============================================================

st.header(
    "1️⃣ Job Description"
)

jd_file = st.file_uploader(
    "Upload a job description",
    type=[
        "pdf",
        "docx",
        "txt",
        "csv",
    ],
)

jd = None

if jd_file:

    try:

        if jd_file.name.lower().endswith(
            ".csv"
        ):

            jd_path = save_to_temp(
                jd_file
            )

            df = pd.read_csv(
                jd_path
            )

            if df.empty:
                st.error(
                    "The CSV is empty."
                )

            else:

                jd_column = pick_text_column(
                    df,
                    "Job description column",
                    "jd_column",
                )

                rows = load_texts_from_csv(
                    jd_path,
                    jd_column,
                )

                if rows:

                    choice = st.selectbox(
                        "Select JD",
                        range(len(rows)),
                        format_func=lambda i:
                        f"Row {i}: "
                        f"{rows[i][1][:70]}...",
                    )

                    jd_id, jd_text = rows[
                        choice
                    ]

                    jd = build_job_description(
                        jd_id,
                        jd_text,
                        title=str(jd_id),
                        keyword_count=keyword_count,
                    )

                    st.success(
                        "Job description loaded."
                    )

        else:

            jd_path = save_to_temp(
                jd_file
            )

            jd_text = extract_text(
                jd_path
            )

            jd = build_job_description(
                jd_file.name,
                jd_text,
                title=jd_file.name,
                keyword_count=keyword_count,
            )

            st.success(
                f"Loaded: {jd_file.name}"
            )

    except Exception as exc:

        st.error(
            f"Failed to process JD: {exc}"
        )


# ============================================================
# Resume Upload
# ============================================================

st.header(
    "2️⃣ Candidate Resumes"
)

resume_files = st.file_uploader(
    "Upload resumes",
    type=[
        "pdf",
        "docx",
        "txt",
        "csv",
    ],
    accept_multiple_files=True,
)

resumes = []

if resume_files:

    for file_index, file in enumerate(
        resume_files
    ):

        try:

            if file.name.lower().endswith(
                ".csv"
            ):

                csv_path = save_to_temp(
                    file
                )

                df = pd.read_csv(
                    csv_path
                )

                if df.empty:
                    continue

                column = pick_text_column(
                    df,
                    f"Resume column · {file.name}",
                    f"resume_col_{file_index}",
                )

                rows = load_texts_from_csv(
                    csv_path,
                    column,
                )

                for identifier, text in rows:

                    resume = build_resume(
                        identifier,
                        text,
                        display_name=identifier,
                    )

                    resumes.append(
                        resume
                    )

            else:

                path = save_to_temp(
                    file
                )

                text = extract_text(
                    path
                )

                resume = build_resume(
                    file.name,
                    text,
                    display_name=file.name,
                )

                resumes.append(
                    resume
                )

        except Exception as exc:

            st.error(
                f"Failed to process "
                f"{file.name}: {exc}"
            )

    if resumes:

        st.success(
            f"✅ {len(resumes)} resume(s) ready."
        )


# ============================================================
# Run
# ============================================================

st.header(
    "3️⃣ Analyze"
)

ready = (
    jd is not None
    and len(resumes) > 0
)

run = st.button(
    "🔍 Analyze & Rank Candidates",
    type="primary",
    use_container_width=True,
    disabled=not ready,
)

if not ready:

    st.caption(
        "Upload a job description and "
        "at least one resume."
    )


# ============================================================
# Ranking
# ============================================================

if run:

    try:

        with st.status(
            "Analyzing candidates...",
            expanded=True,
        ) as status:

            st.write(
                "Generating semantic embeddings..."
            )

            results = rank_resumes(
                jd,
                resumes,
                keyword_count=keyword_count,
            )

            st.write(
                "Calculating requirement matches..."
            )

            if enable_llm:

                st.write(
                    "Generating AI explanations..."
                )

                results = add_justifications(
                    jd,
                    results,
                    top_n=top_n,
                    enabled=True,
                )

            status.update(
                label="Analysis complete!",
                state="complete",
            )

        st.session_state[
            "results"
        ] = results

    except Exception as exc:

        st.error(
            f"Analysis failed: {exc}"
        )

        st.exception(exc)


# ============================================================
# Results
# ============================================================

results = st.session_state.get(
    "results"
)

if results:

    st.divider()

    st.header(
        "🏆 Candidate Ranking"
    )

    scores = [
        float(
            safe_get(
                result,
                "score",
                0.0,
            )
        )
        for result in results
    ]

    top_score = (
        max(scores)
        if scores
        else 0.0
    )

    average_score = (
        sum(scores) / len(scores)
        if scores
        else 0.0
    )

    strong_matches = sum(
        score >= 0.60
        for score in scores
    )

    metrics = st.columns(3)

    with metrics[0]:
        st.metric(
            "Candidates",
            len(results),
        )

    with metrics[1]:
        st.metric(
            "Top Match",
            f"{top_score:.0%}",
        )

    with metrics[2]:
        st.metric(
            "Strong Matches",
            strong_matches,
        )

    st.divider()

    for rank, result in enumerate(
        results,
        start=1,
    ):

        render_candidate(
            rank,
            result,
        )