import re

from rest_framework.exceptions import PermissionDenied

from ..utils import extract_education, extract_experience, extract_skills


def build_parsed_resume_from_candidate(candidate):
    """Build the normalized resume payload used by eligibility and ATS scoring."""
    return {
        "skills": [
            skill.strip().lower()
            for skill in re.split(r"[,\n]+", candidate.skills or "")
            if skill.strip()
        ],
        "experience": candidate.experience or "",
        "education": [],
    }


def build_parsed_resume_from_text(text):
    """Extract and normalize resume information from raw resume text."""
    return {
        "skills": extract_skills(text),
        "experience": extract_experience(text),
        "education": extract_education(text),
    }


def validate_job_owner(user, job):
    """Ensure the authenticated employer owns the requested job."""
    if job.employer != user.employer:
        raise PermissionDenied("Not your job")