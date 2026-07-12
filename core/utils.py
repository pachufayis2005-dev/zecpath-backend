import os
import pdfplumber
from docx import Document


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


def clean_text(text):

    text = text.replace("\n", " ")

    text = " ".join(text.split())

    return text