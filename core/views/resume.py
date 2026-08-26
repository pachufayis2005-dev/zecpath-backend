import re

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Job
from ..permissions import IsCandidate
from ..utils import calculate_ats_score, extract_resume_text
from .helpers import build_parsed_resume_from_text


@extend_schema(
    summary="Parse a resume",
    description=(
        "Uploads and parses a resume file against a specific job, "
        "extracting skills, education, experience, and an ATS match score."
    ),
)
class ResumeParserAPIView(APIView):
    """Extract structured data (skills, education, experience) from an
    uploaded resume and score it against a job."""

    permission_classes = [IsAuthenticated, IsCandidate]

    def post(self, request):

        uploaded_file = request.FILES.get("resume")

        if not uploaded_file:
            return Response(
                {"error": "Resume file required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        job_id = request.data.get("job_id")

        if not job_id:
            return Response(
                {"error": "job_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        job = get_object_or_404(Job, id=job_id)

        clean_text = extract_resume_text(uploaded_file)
        parsed_resume = build_parsed_resume_from_text(clean_text)

        skills = parsed_resume["skills"]
        experience = parsed_resume["experience"]
        education = parsed_resume["education"]

        job_skills = [
            skill.strip().lower()
            for skill in re.split(r"[,\n]+", job.skills)
            if skill.strip()
        ]

        resume_skills = [skill.lower() for skill in skills]

        matched_skills = [skill for skill in job_skills if skill in resume_skills]

        ats_result = calculate_ats_score(job, parsed_resume)

        return Response(
            {
                "filename": uploaded_file.name,
                "job": job.title,
                "job_skills": job_skills,
                "matched_skills": matched_skills,
                "skills": skills,
                "experience": experience,
                "education": education,
                "ats_score": ats_result["score"],
                "clean_text": clean_text,
            },
            status=status.HTTP_200_OK,
        )