import os
import re
import pdfplumber
from docx import Document


# -----------------------------
# Resume Text Extraction
# -----------------------------

def extract_resume_text(file):

    extension = os.path.splitext(file.name)[1].lower()

    text = ""

    if extension == ".pdf":

        with pdfplumber.open(file) as pdf:

            for page in pdf.pages:

                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

    elif extension == ".docx":

        document = Document(file)

        for paragraph in document.paragraphs:
            text += paragraph.text + "\n"

    return clean_text(text)


# -----------------------------
# Clean Text
# -----------------------------

def clean_text(text):

    text = text.replace("\n", " ")
    text = " ".join(text.split())

    return text


# -----------------------------
# Skills Library
# -----------------------------

SKILLS = [

    "python",
    "django",
    "rest api",
    "drf",
    "sql",
    "mysql",
    "postgresql",
    "html",
    "css",
    "javascript",
    "react",
    "git",
    "github",
    "docker",
    "linux",
    "aws",
    "java",
    "c",
    "c++",
]


# -----------------------------
# Extract Skills
# -----------------------------

def extract_skills(text):

    found = []

    lower_text = text.lower()

    for skill in SKILLS:

        if re.search(r"\b" + re.escape(skill) + r"\b", lower_text):
            found.append(skill)

    return found


# -----------------------------
# Experience Extraction
# -----------------------------

def extract_experience(text):

    match = re.search(r"(\d+)\+?\s*years?", text.lower())

    if match:
        return match.group(1) + " years"

    return "Not Found"


# -----------------------------
# Education Extraction
# -----------------------------

def extract_education(text):

    education_keywords = [

        "bca",
        "b.tech",
        "mca",
        "bsc",
        "msc",
        "computer science",
        "engineering",

    ]

    text_lower = text.lower()

    found = []

    for item in education_keywords:

        if item in text_lower:
            found.append(item)

    return found

# -----------------------------
# ATS Score Calculation
# -----------------------------

def calculate_ats_score(job, parsed_resume):

    score = 0

    matched_skills = []

    # -----------------------------
    # Skills (60%)
    # -----------------------------

    import re  # add this at the top of the file if not already there

    job_skills = [
    skill.strip().lower()
    for skill in re.split(r"[,\n]+", job.skills)
    if skill.strip()
    ]
    resume_skills = [
        skill.lower()
        for skill in parsed_resume["skills"]
    ]

    for skill in job_skills:

        if skill in resume_skills:

            matched_skills.append(skill)

    if job_skills:

        skill_score = (
            len(matched_skills)
            /
            len(job_skills)
        ) * 60

    else:

        skill_score = 0

    score += skill_score

    # -----------------------------
    # Experience (30%)
    # -----------------------------

    job_exp = "".join(
        filter(str.isdigit, job.experience)
    )

    resume_exp = "".join(
        filter(str.isdigit, parsed_resume["experience"])
    )

    if job_exp and resume_exp:

        if int(resume_exp) >= int(job_exp):

            score += 30

    # -----------------------------
    # Education (10%)
    # -----------------------------

    if parsed_resume["education"]:

        score += 10

    return {

        "score": round(score, 2),

        "matched_skills": matched_skills

    }