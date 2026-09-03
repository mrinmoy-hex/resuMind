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

def get_rating(score: float) -> tuple[str, str]:

    if score >= 0.75:
        return "Excellent Match", "🟢"

    if score >= 0.60:
        return "Strong Match", "🔵"

    if score >= 0.45:
        return "Moderate Match", "🟠"

    if score >= 0.30:
        return "Weak Match", "🔴"

    return "Poor Match", "⚪"


def save_to_temp(uploaded_file) -> str:

    suffix = Path(uploaded_file.name).suffix

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    ) as tmp:

        tmp.write(uploaded_file.getbuffer())

        return tmp.name


def safe_get(obj, attribute: str, default=None):

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

    guessed_col = guess_text_column(df)

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

    label, icon = get_rating(score)

    with st.container(border=True):

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

            analysis_cols = st.columns(2)

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
# Job Database
# ============================================================

def find_job_database() -> Path | None:

    """
    Look for the internal JD database in a few sensible
    project locations.

    This means the user does not need to upload jd.csv.
    """

    candidates = [
        Path("jd.csv"),
        Path("data/jd.csv"),
        Path("data/job_descriptions.csv"),
        Path("backend/data/jd.csv"),
    ]

    for path in candidates:

        if path.exists() and path.is_file():
            return path

    return None


@st.cache_data
def load_job_database(
    path: str,
) -> pd.DataFrame:

    df = pd.read_csv(path)

    if df.empty:
        raise ValueError(
            "The job database is empty."
        )

    return df


def prepare_job_database(
    df: pd.DataFrame,
) -> tuple[str | None, str | None]:

    """
    Detect the role/title and JD columns.

    Preferred schema:

        position_title
        job_description

    Falls back to common alternatives.
    """

    title_candidates = [
        "position_title",
        "job_title",
        "title",
        "position",
        "role",
    ]

    description_candidates = [
        "job_description",
        "description",
        "job_desc",
        "jd",
        "requirements",
    ]

    title_column = next(
        (
            col
            for col in title_candidates
            if col in df.columns
        ),
        None,
    )

    description_column = next(
        (
            col
            for col in description_candidates
            if col in df.columns
        ),
        None,
    )

    return (
        title_column,
        description_column,
    )


def get_available_roles(
    df: pd.DataFrame,
    title_column: str,
) -> list[str]:

    roles = (
        df[title_column]
        .dropna()
        .astype(str)
        .str.strip()
    )

    roles = roles[
        roles != ""
    ]

    return sorted(
        roles.unique(),
        key=str.lower,
    )


def build_jd_from_role(
    df: pd.DataFrame,
    role: str,
    title_column: str,
    description_column: str,
    keyword_count: int,
):

    """
    Build a JD from every database entry matching the
    selected role.

    If multiple Web Developer rows exist, their
    descriptions are combined instead of arbitrarily
    selecting only the first one.
    """

    role_mask = (
        df[title_column]
        .astype(str)
        .str.strip()
        .str.casefold()
        == role.strip().casefold()
    )

    matches = df.loc[
        role_mask,
        description_column,
    ]

    descriptions = [
        str(text).strip()
        for text in matches.dropna()
        if str(text).strip()
    ]

    if not descriptions:
        return None

    combined_description = "\n\n".join(
        descriptions
    )

    return build_job_description(
        role,
        combined_description,
        title=role,
        keyword_count=keyword_count,
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

**1. Select a role**  
Choose the type of job you're
screening for.

**2. Understand**  
ResuMind loads the relevant
job requirements.

**3. Match**  
Compare job requirements
against candidate evidence.

**4. Rank**  
Calculate a weighted score.

**5. Explain**  
Use AI to explain the result.
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
# Job Target
# ============================================================

st.header(
    "Target Job"
)

jd = None

# ------------------------------------------------------------
# Preferred path: internal job database
# ------------------------------------------------------------

job_database_path = find_job_database()

if job_database_path:

    try:

        job_df = load_job_database(
            str(job_database_path)
        )

        title_column, description_column = (
            prepare_job_database(job_df)
        )

        if not title_column:

            st.error(
                "The job database does not contain "
                "a recognizable job title column."
            )

            st.caption(
                "Expected something like "
                "`position_title`."
            )

        elif not description_column:

            st.error(
                "The job database does not contain "
                "a recognizable job description column."
            )

            st.caption(
                "Expected something like "
                "`job_description`."
            )

        else:

            roles = get_available_roles(
                job_df,
                title_column,
            )

            st.write(
                "Choose the type of position you're "
                "screening candidates for."
            )

            selected_role = st.selectbox(
                "Job role",
                roles,
                index=0 if roles else None,
                placeholder="Search or select a role...",
            )

            if selected_role:

                jd = build_jd_from_role(
                    job_df,
                    selected_role,
                    title_column,
                    description_column,
                    keyword_count,
                )

                if jd:

                    st.success(
                        f"✓ Using requirements for "
                        f"**{selected_role}**"
                    )

                    st.caption(
                        "ResuMind automatically selected "
                        "the relevant job descriptions "
                        "from its internal database."
                    )

                else:

                    st.error(
                        "No usable job description was "
                        "found for this role."
                    )

    except Exception as exc:

        st.error(
            f"Failed to load job database: {exc}"
        )

else:

    st.info(
        "No internal job database was found. "
        "You can upload a custom job description below."
    )


# ------------------------------------------------------------
# Custom JD fallback
# ------------------------------------------------------------

with st.expander(
    "📄 Use a custom job description instead",
    expanded=not bool(job_database_path),
):

    st.caption(
        "Use this when you have a specific job posting "
        "that isn't in the ResuMind job database."
    )

    custom_jd_file = st.file_uploader(
        "Upload custom JD",
        type=[
            "pdf",
            "docx",
            "txt",
            "csv",
        ],
        key="custom_jd",
    )

    if custom_jd_file:

        try:

            if custom_jd_file.name.lower().endswith(
                ".csv"
            ):

                custom_jd_path = save_to_temp(
                    custom_jd_file
                )

                custom_df = pd.read_csv(
                    custom_jd_path
                )

                if custom_df.empty:

                    st.error(
                        "The CSV is empty."
                    )

                else:

                    custom_column = pick_text_column(
                        custom_df,
                        "Custom JD column",
                        "custom_jd_column",
                    )

                    rows = load_texts_from_csv(
                        custom_jd_path,
                        custom_column,
                    )

                    if rows:

                        choice = st.selectbox(
                            "Select job description",
                            range(len(rows)),
                            format_func=lambda i:
                            f"Row {i}: "
                            f"{rows[i][1][:70]}...",
                            key="custom_jd_choice",
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

            else:

                custom_jd_path = save_to_temp(
                    custom_jd_file
                )

                custom_jd_text = extract_text(
                    custom_jd_path
                )

                jd = build_job_description(
                    custom_jd_file.name,
                    custom_jd_text,
                    title=custom_jd_file.name,
                    keyword_count=keyword_count,
                )

            if jd:

                st.success(
                    f"✓ Custom job description loaded: "
                    f"{custom_jd_file.name}"
                )

        except Exception as exc:

            st.error(
                f"Failed to process custom JD: {exc}"
            )


# ============================================================
# Resume Upload
# ============================================================

st.header(
    "Candidate Resumes"
)

st.write(
    "Upload one or more resumes to compare "
    "against the selected role."
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

    if jd is None and not resumes:
        st.caption(
            "Choose a job role and upload at least "
            "one resume."
        )

    elif jd is None:
        st.caption(
            "Choose a target job role before analyzing."
        )

    elif not resumes:
        st.caption(
            "Upload at least one resume before analyzing."
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

        # Store selected role for result display.
        st.session_state[
            "selected_role"
        ] = getattr(
            jd,
            "title",
            None,
        )

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

    selected_role = st.session_state.get(
        "selected_role"
    )

    if selected_role:

        st.caption(
            f"Results for: **{selected_role}**"
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

