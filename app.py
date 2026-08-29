import streamlit as st
from backend.ingestion import extract_text
from backend.extraction.jd_parser import build_job_description
from backend.extraction.structurer import build_resume
from backend.matching.scorer import rank_resumes


st.title("Resume Screener")
st.caption("An AI-powered resume screening tool - build by <mr1nm0y/>")

jd_file = st.file_uploader("Upload Job Description", type=["pdf", "docx", "txt"])
resume_files = st.file_uploader("Upload Resumes", type=["pdf", "docx", "txt"], accept_multiple_files=True)

if st.button("Rank Candidates") and jd_file and resume_files:
    # Streamlit gives uploaded files as in-memory objects, not disk paths —
    # so we save them to a temp location first since our parsers expect file paths.
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(jd_file.name)[1]) as tmp:
        tmp.write(jd_file.read())
        jd_path = tmp.name
    jd_text = extract_text(jd_path)
    jd = build_job_description(jd_path, jd_text, title=jd_file.name)

    resumes = []
    for f in resume_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(f.name)[1]) as tmp:
            tmp.write(f.read())
            r_path = tmp.name
        r_text = extract_text(r_path)
        resumes.append(build_resume(r_path, r_text))

    results = rank_resumes(jd, resumes)

    st.subheader("Ranked Candidates")
    for r in results:
        st.write(f"**{r.resume.candidate_name}** — score: {r.score:.3f}")