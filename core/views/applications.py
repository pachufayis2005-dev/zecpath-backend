import logging

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Application, InterviewCall, Job, SavedJob
from ..permissions import IsCandidate, IsEmployer
from ..serializers import ApplicationSerializer, JobSerializer, SavedJobSerializer
from ..services import AccessValidationService
from ..services.subscription_service import can_view_ai_analytics
from ..services_py import (
    application_submitted_template,
    auto_shortlist,
    check_application_eligibility,
    check_candidate_eligibility,
    create_ai_interview_session,
    process_pending_applications,
    rejected_template,
    shortlisted_template,
)
from ..tasks import process_interview_calls, send_email_task
from ..throttles import PremiumAPIRateThrottle
from ..utils import calculate_ats_score
from .helpers import build_parsed_resume_from_candidate, validate_job_owner

logger = logging.getLogger(__name__)


@extend_schema(
    summary="Apply to a job",
    description=(
        "Candidate applies to a specific job posting by job ID. "
        "Requires an uploaded resume on the candidate's profile."
    ),
    examples=[
        OpenApiExample(
            "Apply request",
            value={"cover_letter": "I am excited to apply for this role..."},
            request_only=True,
        )
    ],
)
class ApplyJobAPIView(APIView):
    """Submit a job application as a candidate."""

    permission_classes = [IsAuthenticated, IsCandidate]

    def post(self, request, pk):

        job = get_object_or_404(Job, id=pk)

        if job.status != Job.ACTIVE:
            return Response(
                {"error": "Job is closed"}, status=status.HTTP_400_BAD_REQUEST
            )

        if Application.objects.filter(
            candidate=request.user.candidate, job=job
        ).exists():
            return Response(
                {"error": "Already applied"}, status=status.HTTP_400_BAD_REQUEST
            )

        resume = ""
        if request.user.candidate.resume:
            resume = str(request.user.candidate.resume)

        parsed_resume = build_parsed_resume_from_candidate(request.user.candidate)

        eligible = check_candidate_eligibility(job, parsed_resume)

        if not eligible:
            return Response(
                {"error": "Candidate is not eligible for this job."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ats_result = calculate_ats_score(job, parsed_resume)

        application = Application.objects.create(
            candidate=request.user.candidate,
            job=job,
            resume_snapshot=resume,
            ats_score=ats_result["score"],
        )

        auto_shortlist(application)

        application.refresh_from_db()

        interview_ready = check_application_eligibility(application)

        if interview_ready:
            logger.debug(
                "Application %s is eligible for interview scheduling.", application.id
            )

            InterviewCall.objects.create(
                application=application,
                status=InterviewCall.QUEUED,
            )

            create_ai_interview_session(application)

            process_interview_calls.delay()
        else:
            logger.debug(
                "Application %s is not eligible for interview scheduling.",
                application.id,
            )

        subject, message = application_submitted_template(
            request.user.username,
            job.title,
        )

        send_email_task.delay(
            request.user.email,
            subject,
            message,
        )

        serializer = ApplicationSerializer(application)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ApplicationHistoryAPIView(APIView):

    permission_classes = [IsAuthenticated, IsCandidate]

    def get(self, request):

        applications = (
            Application.objects.filter(candidate=request.user.candidate)
            .select_related("job")
            .order_by("-applied_at")
        )

        serializer = ApplicationSerializer(applications, many=True)

        return Response(serializer.data)


class AppliedJobsAPIView(APIView):

    permission_classes = [IsAuthenticated, IsCandidate]

    def get(self, request):

        applications = Application.objects.filter(
            candidate=request.user.candidate
        ).select_related("job")

        jobs = [application.job for application in applications]

        serializer = JobSerializer(jobs, many=True)

        return Response(serializer.data)


class ApplicationStatusUpdateAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    def patch(self, request, pk):

        application = get_object_or_404(
            Application.objects.select_related("job", "candidate"), id=pk
        )

        if application.job.employer != request.user.employer:
            return Response(
                {"error": "Not your application"}, status=status.HTTP_403_FORBIDDEN
            )

        new_status = request.data.get("status")

        valid_statuses = [
            Application.APPLIED,
            Application.SHORTLISTED,
            Application.INTERVIEW_SCHEDULED,
            Application.REJECTED,
            Application.SELECTED,
        ]

        if new_status not in valid_statuses:
            return Response(
                {"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST
            )

        application.status = new_status
        application.save()

        if new_status == Application.SHORTLISTED:
            subject, message = shortlisted_template(
                application.candidate.user.username,
                application.job.title,
            )
            send_email_task.delay(application.candidate.user.email, subject, message)

        elif new_status == Application.REJECTED:
            subject, message = rejected_template(
                application.candidate.user.username,
                application.job.title,
            )
            send_email_task.delay(application.candidate.user.email, subject, message)

        return Response(
            {"message": "Application status updated", "status": application.status}
        )


class ApplicantListAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    def get(self, request, pk):

        job = get_object_or_404(Job, id=pk)

        validate_job_owner(request.user, job)

        applications = Application.objects.filter(job=job)

        status_filter = request.GET.get("status")
        if status_filter:
            applications = applications.filter(status=status_filter)

        search = request.GET.get("search")
        if search:
            applications = applications.filter(
                candidate__user__username__icontains=search
            )

        applications = applications.select_related("candidate", "candidate__user")

        serializer = ApplicationSerializer(applications, many=True)

        return Response(serializer.data)


class ApplicationCountAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    def get(self, request, pk):

        job = get_object_or_404(Job, id=pk)

        validate_job_owner(request.user, job)

        total = Application.objects.filter(job=job).count()
        shortlisted = Application.objects.filter(
            job=job, status=Application.SHORTLISTED
        ).count()
        rejected = Application.objects.filter(
            job=job, status=Application.REJECTED
        ).count()
        selected = Application.objects.filter(
            job=job, status=Application.SELECTED
        ).count()

        return Response(
            {
                "job": job.title,
                "total_applications": total,
                "shortlisted": shortlisted,
                "rejected": rejected,
                "selected": selected,
            }
        )


class ShortlistRatioAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    def get(self, request, pk):

        job = get_object_or_404(Job, id=pk)

        validate_job_owner(request.user, job)

        total = Application.objects.filter(job=job).count()
        shortlisted = Application.objects.filter(
            job=job, status=Application.SHORTLISTED
        ).count()

        ratio = 0 if total == 0 else round((shortlisted / total) * 100, 2)

        return Response(
            {
                "job": job.title,
                "total_applications": total,
                "shortlisted": shortlisted,
                "shortlist_ratio": f"{ratio}%",
            }
        )


class SavedJobsAPIView(APIView):

    permission_classes = [IsAuthenticated, IsCandidate]

    def get(self, request):

        saved_jobs = SavedJob.objects.filter(
            candidate=request.user.candidate
        ).select_related("job")

        serializer = SavedJobSerializer(saved_jobs, many=True)

        return Response(serializer.data)


class SaveJobAPIView(APIView):

    permission_classes = [IsAuthenticated, IsCandidate]

    def post(self, request, pk):

        job = get_object_or_404(Job, id=pk)

        if SavedJob.objects.filter(candidate=request.user.candidate, job=job).exists():
            return Response(
                {"error": "Job already saved"}, status=status.HTTP_400_BAD_REQUEST
            )

        saved_job = SavedJob.objects.create(candidate=request.user.candidate, job=job)

        serializer = SavedJobSerializer(saved_job)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CandidateDashboardAPIView(APIView):

    permission_classes = [IsAuthenticated, IsCandidate]

    def get(self, request):

        applied_jobs = Application.objects.filter(
            candidate=request.user.candidate
        ).count()
        saved_jobs = SavedJob.objects.filter(candidate=request.user.candidate).count()

        return Response(
            {
                "candidate": request.user.username,
                "applied_jobs": applied_jobs,
                "saved_jobs": saved_jobs,
            }
        )


class ApplicationTimelineAPIView(APIView):

    permission_classes = [IsAuthenticated, IsCandidate]

    def get(self, request):

        applications = (
            Application.objects.filter(candidate=request.user.candidate)
            .select_related("job")
            .order_by("-applied_at")
        )

        data = [
            {
                "job": application.job.title,
                "company": application.job.employer.company_name,
                "status": application.status,
                "applied_at": application.applied_at,
                "last_updated": application.updated_at,
            }
            for application in applications
        ]

        return Response(data)


class InterviewStatusAPIView(APIView):

    permission_classes = [IsAuthenticated, IsCandidate]

    def get(self, request):

        applications = Application.objects.filter(
            candidate=request.user.candidate
        ).select_related("job")

        data = [
            {
                "job": application.job.title,
                "status": application.status,
                "updated_at": application.updated_at,
            }
            for application in applications
            if application.status
            in [
                Application.SHORTLISTED,
                Application.INTERVIEW_SCHEDULED,
                Application.SELECTED,
            ]
        ]

        return Response(data)


class UpdateApplicationStatusAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    def patch(self, request, pk):

        application = get_object_or_404(Application, id=pk)

        AccessValidationService.validate_application_job_owner(
            request.user, application
        )

        new_status = request.data.get("status")

        if new_status not in [Application.SHORTLISTED, Application.REJECTED]:
            return Response(
                {"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST
            )

        application.status = new_status
        application.save()

        if new_status == Application.SHORTLISTED:
            subject, message = shortlisted_template(
                application.candidate.user.username,
                application.job.title,
            )
            send_email_task.delay(request.user.email, subject, message)

        elif new_status == Application.REJECTED:
            subject, message = rejected_template(
                application.candidate.user.username,
                application.job.title,
            )
            send_email_task.delay(request.user.email, subject, message)

        serializer = ApplicationSerializer(application)

        return Response(serializer.data)


class ProcessApplicationsAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    def post(self, request):

        updated = process_pending_applications()

        return Response(
            {
                "message": "Batch processing completed.",
                "processed_applications": updated,
            }
        )


class RankedCandidatesAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    throttle_classes = [PremiumAPIRateThrottle]

    def get(self, request, pk):

        employer = request.user.employer

        if not can_view_ai_analytics(employer):
            return Response(
                {
                    "error": "Your subscription does not allow access to candidate ranking."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        job = get_object_or_404(Job, id=pk)

        validate_job_owner(request.user, job)

        applications = (
            Application.objects.filter(job=job)
            .select_related("candidate", "candidate__user")
            .order_by("-ats_score")
        )

        data = [
            {
                "candidate": application.candidate.user.username,
                "ats_score": application.ats_score,
                "suitability": f"{application.ats_score}%",
                "status": application.status,
                "applied_at": application.applied_at,
            }
            for application in applications
        ]

        return Response(
            {
                "job": job.title,
                "total_candidates": len(data),
                "ranked_candidates": data,
            },
            status=status.HTTP_200_OK,
        )