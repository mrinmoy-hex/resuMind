# 🧠 ResuMind

**AI-powered resume screening and candidate ranking system.**

ResuMind analyzes resumes against job requirements, calculates a multi-factor match score, ranks candidates, and uses AI to explain why a candidate is a good or weak fit.

The goal is simple:

> **Turn a stack of resumes into an understandable, evidence-based candidate ranking.**

---

## ✨ Features

* 📄 **Resume ingestion**

  * Supports PDF, DOCX, TXT, and CSV resumes
  * Extracts and structures candidate information automatically

* 🎯 **Job-role based matching**

  * Select a target role such as `Web Developer`, `Python Developer`, or `Data Analyst`
  * Automatically retrieves relevant job requirements from the internal job database

* 📋 **Custom job descriptions**

  * Upload a specific JD when the internal database isn't suitable
  * Supports PDF, DOCX, TXT, and CSV

* 🧠 **Semantic matching**

  * Goes beyond simple keyword matching
  * Compares the meaning of resume content with job requirements

* 🛠️ **Requirement matching**

  * Identifies matched requirements
  * Identifies missing or weak requirements

* 📊 **Multi-factor scoring**

  * Skills
  * Semantic similarity
  * Experience

* 🏆 **Candidate ranking**

  * Ranks candidates from strongest to weakest match
  * Provides an overall match percentage

* 🤖 **AI explanations**

  * Generates explanations for candidate rankings
  * Highlights strengths and concerns

* ⚙️ **Configurable analysis**

  * Adjustable number of JD requirements
  * Optional AI-generated analysis
  * Configurable number of top candidates to analyze

---

## 🖥️ How It Works

```text
                    ┌──────────────────┐
                    │   Job Database   │
                    │     jd.csv       │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   Select Role    │
                    │ "Web Developer"  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Build Job        │
                    │ Description      │
                    └────────┬─────────┘
                             │
                             │
┌───────────────┐            │
│ Resume Files  │            │
│ PDF/DOCX/TXT  │            │
│ CSV           │            │
└───────┬───────┘            │
        │                    │
        ▼                    ▼
┌─────────────────────────────────────┐
│           Text Extraction           │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│        Resume Structuring           │
│                                     │
│ Name • Skills • Experience • etc.   │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│          Matching Engine            │
│                                     │
│ Skills + Semantic + Experience      │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│          Candidate Ranking          │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│        Optional AI Analysis         │
│                                     │
│ Strengths • Concerns • Explanation  │
└──────────────────┬──────────────────┘
                   │
                   ▼
             🏆 Results
```

---



# 🔄 Processing Pipeline

## 1. Job Selection

ResuMind can use an internal job-description database.

For example:

```csv
position_title,job_description
Web Developer,"Develop and maintain web applications..."
Python Developer,"Build Python applications and APIs..."
Data Analyst,"Analyze datasets and create reports..."
```

The user only needs to select:

```text
Web Developer
```

ResuMind automatically finds the associated job descriptions.

If multiple descriptions exist for the same role, they can be combined to provide a broader representation of the role.

---

## 2. Resume Extraction

Uploaded resumes are converted into text.

Supported formats:

```text
PDF
DOCX
TXT
CSV
```

For CSV files containing multiple resumes, ResuMind can identify the relevant text column and process individual candidate records.

---

## 3. Resume Structuring

Raw resume text is converted into a structured representation.

Conceptually:

```python
Resume(
    candidate_name="Candidate",
    skills=[...],
    experience_years=...,
    ...
)
```

This structured representation makes the matching process more reliable than comparing raw documents directly.

---

## 4. Job Description Structuring

The selected job description is processed into a structured representation containing relevant requirements.

The number of extracted requirements can be configured through the application.

---

## 5. Candidate Matching

Each candidate is evaluated against the selected job.

ResuMind considers multiple signals rather than relying exclusively on exact keyword matches.

### Skills Score

Measures how well the candidate's skills satisfy the identified job requirements.

### Semantic Score

Measures conceptual similarity between the candidate's experience and the job requirements.

This helps recognize related experience even when the exact wording differs.

### Experience Score

Considers the candidate's detected experience relative to the requirements.

---

## 6. Overall Score

The individual signals are combined into an overall candidate score.

The exact weighting is implemented by the matching backend.

The resulting score is used to rank candidates.

Example:

```text
Candidate A    87%
Candidate B    74%
Candidate C    61%
Candidate D    43%
```

---

## 7. AI Explanation

AI analysis can optionally be enabled.

For the highest-ranked candidates, ResuMind can generate:

* Overall justification
* Strengths
* Concerns

Example:

```text
Strong Match

The candidate has strong Python and API development
experience that aligns well with the selected role.

Strengths:
✓ Python
✓ REST APIs
✓ Git

Concerns:
⚠ Limited Docker experience
⚠ No demonstrated React experience
```

---

# 📊 Match Rating

ResuMind currently categorizes match scores as:

| Score | Rating             |
| ----: | ------------------ |
| ≥ 75% | 🟢 Excellent Match |
| ≥ 60% | 🔵 Strong Match    |
| ≥ 45% | 🟠 Moderate Match  |
| ≥ 30% | 🔴 Weak Match      |
| < 30% | ⚪ Poor Match       |

These ratings provide a quick interpretation of the numerical score.

---

#  Using ResuMind

## Step 1 — Start the application

Run:

```bash
streamlit run app.py
```

The application will open in your browser.

---

## Step 2 — Select a target role

Choose the type of position you're screening for.

For example:

```text
Web Developer
Python Developer
Data Analyst
Software Engineer
```

The application automatically retrieves the relevant requirements from the internal job database.

---

## Step 3 — Upload resumes

Upload one or more candidate resumes.

Supported formats:

```text
.pdf
.docx
.txt
.csv
```

---

## Step 4 — Configure analysis

Optional settings include:

* AI analysis
* Number of candidates receiving AI analysis
* Number of JD requirements

---

## Step 5 — Analyze

Click:

```text
 Analyze & Rank Candidates
```

ResuMind processes the candidates and generates the ranking.

---

## Step 6 — Review results

Each candidate receives:

* Overall match score
* Match rating
* Skills score
* Semantic score
* Experience score
* Matched requirements
* Missing/weak requirements
* Detected experience
* Optional AI explanation

---

# Job Database

The internal job database allows users to select roles without needing to understand the underlying CSV structure.

A recommended schema is:

```csv
position_title,job_description
Web Developer,"..."
Python Developer,"..."
Data Analyst,"..."
```

The application looks for the job database in locations such as:

```text
jd.csv
data/jd.csv
data/job_descriptions.csv
backend/data/jd.csv
```

The preferred columns are:

```text
position_title
job_description
```

Common alternative column names are also detected.

---

# Custom Job Descriptions

ResuMind also supports custom job descriptions.

This is useful when a recruiter or user has a specific job posting that isn't represented in the internal database.

Use:

```text
 Use a custom job description instead
```

Then upload the JD.

This creates two possible workflows:

```text
                    ResuMind
                       │
              ┌────────┴────────┐
              │                 │
        Internal JD         Custom JD
          Database          Upload
              │                 │
              └────────┬────────┘
                       │
                       ▼
                Matching Engine
```

---

# Configuration

Environment variables can be loaded using `.env`.

Create a `.env` file:

```env
# Add required API credentials here
# Example:
# OPENAI_API_KEY=your_key_here
```

Do **not** commit `.env` or API keys to Git.

Add this to `.gitignore`:

```gitignore
.env
__pycache__/
*.pyc
.venv/
venv/
myenv/
```

---

# Installation

## Clone the repository

```bash
git clone https://github.com/mrinmoy-hex/resuMind.git
cd resuMind
```

## Create a virtual environment

Linux/macOS:

```bash
python -m venv myenv
source myenv/bin/activate
```

Windows:

```powershell
python -m venv myenv
myenv\Scripts\activate
```

## Install dependencies

```bash
pip install -r requirements.txt
```

## Configure environment variables

Create:

```text
.env
```

and add the required API configuration.

## Run

```bash
streamlit run app.py
```

---

# Development

ResuMind is being developed with an emphasis on gradually moving beyond simple keyword-based resume screening.

The project currently combines:

```text
Document Processing
       +
Information Extraction
       +
Semantic Matching
       +
Rule-based Scoring
       +
LLM-generated Explanations
```

This makes the system useful not only for producing a score, but also for explaining the reasoning behind that score.

---


# Tech Stack

| Technology                | Purpose                |
| ------------------------- | ---------------------- |
| Python                    | Core application       |
| Streamlit                 | Web interface          |
| Pandas                    | CSV/data processing    |
| PDF/DOCX extraction tools | Document ingestion     |
| Semantic embeddings       | Meaning-based matching |
| LLM                       | Candidate explanations |
| Git/GitHub                | Version control        |

---


# Author

> **Mrinmoy Deka**

GitHub:
**[@mrinmoy-hex](https://github.com/mrinmoy-hex)**
---


