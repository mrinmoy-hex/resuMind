import os
import tempfile

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from backend.ingestion import extract_text, load_texts_from_csv
from backend.extraction.jd_parser import build_job_description
from backend.extraction.structurer import build_resume
from backend.matching.scorer import rank_resumes, add_justifications

load_dotenv()

ENABLE_LLM_JUSTIFICATION = True

st.set_page_config(page_title="Resume Screener", page_icon="📄", layout="wide")
st.title("📄 Resume Screener")
st.caption("An AI-powered resume screening tool — built by <mr1nm0y/>")


def save_to_temp(uploaded_file) -> str:
    suffix = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        return tmp.name


# ---- Job Description input ----
col1, col2 = st.columns(2)

with col1:
    jd_file = st.file_uploader(
        "Upload Job Description (single file, or a CSV of JDs)",
        type=["pdf", "docx", "txt", "csv"],
    )

    jd = None
    if jd_file:
        if jd_file.name.endswith(".csv"):
            jd_path = save_to_temp(jd_file)
            df_preview = pd.read_csv(jd_path)
            jd_column = st.selectbox(
                "Which column holds JD text?",
                options=df_preview.columns.tolist(),
                key="jd_col",
            )
            rows = load_texts_from_csv(jd_path, text_column=jd_column)
            titles = [f"{i}: {row[0]}" for i, row in enumerate(rows)]
            choice = st.selectbox(
                "Pick a JD row", options=range(len(rows)), format_func=lambda i: titles[i]
            )
            jd_id, jd_text = rows[choice]
            jd = build_job_description(jd_id, jd_text, title=jd_id)
        else:
            jd_path = save_to_temp(jd_file)
            jd_text = extract_text(jd_path)
            jd = build_job_description(jd_path, jd_text, title=jd_file.name)

# ---- Resume input ----
with col2:
    resume_files = st.file_uploader(
        "Upload Resumes (multiple files, or a single CSV of resumes)",
        type=["pdf", "docx", "txt", "csv"],
        accept_multiple_files=True,
    )

resumes = []
if resume_files:
    for f in resume_files:
        if f.name.endswith(".csv"):
            csv_path = save_to_temp(f)
            df_preview = pd.read_csv(csv_path)
            resume_column = st.selectbox(
                "Which column holds resume text?",
                options=df_preview.columns.tolist(),
                key=f"resume_col_{f.name}",
            )
            rows = load_texts_from_csv(csv_path, text_column=resume_column)
            for ident, text in rows:
                resumes.append(build_resume(ident, text))
        else:
            r_path = save_to_temp(f)
            r_text = extract_text(r_path)
            resumes.append(build_resume(r_path, r_text))

st.caption(f"{len(resumes)} resume(s) loaded" if resumes else "")

# ---- Run ranking ----
if st.button("Rank Candidates", type="primary"):
    if not jd or not resumes:
        st.warning("Please provide both a job description and at least one resume.")
    else:
        with st.spinner("Ranking candidates..."):
            results = rank_resumes(jd, resumes)
            results = add_justifications(jd, results, top_n=5, enabled=ENABLE_LLM_JUSTIFICATION)

        st.subheader("Ranked Candidates")
        for r in results:
            with st.container(border=True):
                st.write(f"**{r.resume.candidate_name}** — score: `{r.score:.3f}`")
                st.progress(min(max(r.score, 0.0), 1.0))
                if r.justification:
                    st.caption(r.justification)


def add_footer():
    st.markdown(
        """
        <style>
        .footer {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background-color: #0E1117; color: #888; text-align: center;
            padding: 8px 0; font-size: 14px; border-top: 1px solid #2A2D34;
        }
        .footer a { color: #4F46E5; text-decoration: none; }
        </style>
        <div class="footer">Built by Mrinmoy · <a href="https://github.com/YOUR_GITHUB_USERNAME" target="_blank">GitHub</a></div>
        """,
        unsafe_allow_html=True,
    )


add_footer()