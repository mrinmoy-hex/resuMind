import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

from backend.ingestion import extract_text
from backend.extraction.jd_parser import build_job_description
from backend.extraction.structurer import build_resume
from backend.matching.scorer import rank_resumes, add_justifications

load_dotenv()

# Flip to False to instantly disable LLM justifications if the API misbehaves
ENABLE_LLM_JUSTIFICATION = True

st.set_page_config(
    page_title="Resume Screener",
    page_icon="📄",
    layout="wide",
)

st.title("Resume Screener")
st.caption("An AI-powered resume screening tool — built by <mr1nm0y/>")

col1, col2 = st.columns(2)
with col1:
    jd_file = st.file_uploader("Upload Job Description", type=["pdf", "docx", "txt"])
with col2:
    resume_files = st.file_uploader(
        "Upload Resumes", type=["pdf", "docx", "txt"], accept_multiple_files=True
    )


def save_to_temp(uploaded_file) -> str:
    """Streamlit gives uploaded files as in-memory objects, not disk paths —
    our parsers expect file paths, so we write each upload to a temp file first."""
    suffix = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        return tmp.name


if st.button("Rank Candidates", type="primary"):
    if not jd_file or not resume_files:
        st.warning("Please upload both a job description and at least one resume.")
    else:
        with st.spinner("Reading documents and ranking candidates..."):
            jd_path = save_to_temp(jd_file)
            jd_text = extract_text(jd_path)
            jd = build_job_description(jd_path, jd_text, title=jd_file.name)

            resumes = []
            for f in resume_files:
                r_path = save_to_temp(f)
                r_text = extract_text(r_path)
                resumes.append(build_resume(r_path, r_text))

            results = rank_resumes(jd, resumes)
            results = add_justifications(
                jd, results, top_n=5, enabled=ENABLE_LLM_JUSTIFICATION
            )

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
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #0E1117;
            color: #888;
            text-align: center;
            padding: 8px 0;
            font-size: 14px;
            border-top: 1px solid #2A2D34;
        }
        .footer a { color: #4F46E5; text-decoration: none; }
        </style>
        <div class="footer">
            Built by Mrinmoy · <a href="https://github.com/mrinmoy-hex" target="_blank">GitHub</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


add_footer()