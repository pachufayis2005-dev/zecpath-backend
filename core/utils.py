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