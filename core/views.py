from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.shortcuts import render
from django.conf import settings
from django.utils import timezone
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.http import JsonResponse
import json

import re
from .services import (AnswerEvaluator,SchedulingEngine,AnalyticsService,AuditService,AccessValidationService)
from rest_framework_simplejwt.tokens import RefreshToken
from core.services.subscription_service import (can_view_analytics,can_post_job)
from core.services.billing_service import BillingService
from core.services.subscription_service import (get_subscription_status,)
from core.services.analytics_service import AnalyticsService
from core.services.subscription_service import can_view_ai_analytics
from core.services.subscription_service import can_post_job
from core.services.payment_service import PaymentService
from .security import log_unauthorized_access
from .services.report_service import CandidateReportService
from .utils import extract_resume_text,calculate_ats_score
from .services_py import (
    auto_shortlist,
    check_candidate_eligibility,
    process_pending_applications,
    application_submitted_template,
    shortlisted_template,
    rejected_template,
    check_application_eligibility,
    create_ai_interview_session,
)
from .tasks import (send_email_task,process_interview_calls,send_interview_reminders)
from core.throttles import (LoginRateThrottle,PremiumAPIRateThrottle,)
from .pagination import JobPagination
from .profile_serializers import (CandidateProfileSerializer,EmployerProfileSerializer,)
from .permissions import IsCandidate, IsEmployer, IsAdmin
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .auth_serializers import SignupSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .serializers import (ApplicationSerializer,SavedJobSerializer,AuditLogSerializer,SubmitAnswerSerializer,)
from .models import (
    User,
    Job,
    Candidate,
    Employer,
    Application,
    SavedJob,
    AuditLog,
    InterviewCall,
    AIAnswer,
    AvailabilitySlot,
    InterviewSchedule,
    PaymentTransaction,
    BillingHistory,
    RefundRecord,
    FinancialAuditLog,
)
from .serializers import (JobSerializer,AvailabilitySlotSerializer,InterviewScheduleSerializer,PaymentTransactionSerializer,
BillingHistorySerializer,RefundRecordSerializer,FinancialAuditLogSerializer,)
from .utils import (
    extract_resume_text,
    extract_skills,
    extract_experience,
    extract_education,
)

from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema, OpenApiExample


@extend_schema(
    summary="Login and get JWT tokens",
    description="Authenticate with username and password. Returns access and refresh tokens.",
    examples=[
        OpenApiExample(
            'Login request',
            value={"username": "john_doe", "password": "yourpassword123"},
            request_only=True,
        )
    ]
)
class LoginAPIView(TokenObtainPairView):
    """Authenticate a user and return JWT access + refresh tokens."""
    throttle_classes = [LoginRateThrottle]


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(
                {"error": "Invalid or missing refresh token"},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(
    summary="List all job postings",
    description="Returns a list of active job postings available on the platform."
)
class JobListAPIView(APIView):
    """Get a list of all active jobs."""

    def get(self, request):

        jobs = Job.objects.select_related(
            "employer"
        ).all()

        # Search

        search = request.GET.get("search")

        if search:
            jobs = jobs.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(skills__icontains=search)
    )

        # Skill filter
        skill = request.GET.get(
        "skill"
            )

        if skill:
            jobs = jobs.filter(
            skills__icontains=skill
            )

        # Experience filter
        experience = request.GET.get(
    "experience"
)

        if experience:
            jobs = jobs.filter(
            experience__icontains=experience
            )

        # Salary filter
        salary = request.GET.get(
    "salary"
)

        if salary:
            jobs = jobs.filter(
            salary__gte=salary
            )

        # Location filter
        location = request.GET.get(
            "location"
            )

        if location:
            jobs = jobs.filter(
            location__icontains=location
            )

        # Job type filter
        job_type = request.GET.get(
            "job_type"
            )

        if job_type:
            jobs = jobs.filter(
            job_type=job_type
            )

        # Status filter
        status_filter = request.GET.get("status")

        if status_filter:
            jobs = jobs.filter(
                status=status_filter
            )

        # Date filter
        date_filter = request.GET.get("date")

        if date_filter:
            jobs = jobs.filter(
                created_at__date=date_filter
            )

        paginator = JobPagination()

        paginated_jobs = paginator.paginate_queryset(
            jobs,
            request
        )

        serializer = JobSerializer(
            paginated_jobs,
            many=True
        )

        return paginator.get_paginated_response(
            serializer.data
        )


class JobCreateAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsEmployer
    ]

    def post(self, request):

        employer = request.user.employer

        if not can_post_job(employer):
            return Response(
                {
                    "error": "Your subscription does not allow you to post another job."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = JobSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save(
                employer=employer
            )

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class FeaturedJobAPIView(APIView):

    def get(self, request):

        jobs = Job.objects.filter(
            status=Job.ACTIVE,
            is_featured=True
        ).order_by(
            "-created_at"
        )

        serializer = JobSerializer(
            jobs,
            many=True
        )

        return Response(serializer.data)

class LatestJobAPIView(APIView):

    @method_decorator(cache_page(60 * 5))
    def get(self, request):

        jobs = Job.objects.filter(
            status=Job.ACTIVE
        ).order_by(
            "-created_at"
        )[:5]

        serializer = JobSerializer(
            jobs,
            many=True
        )

        return Response(
            serializer.data
        )

class UserTestAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "message": "Protected API Working",
            "user": request.user.username,
            "role": request.user.role,
        })
class SignupAPIView(APIView):

    def post(self, request):

        serializer = SignupSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
class AdminAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin
    ]

    def get(self, request):
        return Response({
            "message": "Admin Access Granted"
        })
    




class CandidateProfileAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsCandidate
    ]

    def get(self, request):

        profile = request.user.candidate

        serializer = CandidateProfileSerializer(
            profile
        )

        return Response(serializer.data)

    def put(self, request):

        profile = request.user.candidate

        serializer = CandidateProfileSerializer(
            profile,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    def delete(self, request):

        profile = request.user.candidate

        profile.is_active = False

        profile.save()

        return Response({
            "message": "Candidate profile deactivated"
    })

class EmployerProfileAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsEmployer
    ]

    def get(self, request):

        profile = request.user.employer

        serializer = EmployerProfileSerializer(
            profile
        )

        return Response(serializer.data)

    def put(self, request):

        profile = request.user.employer

        serializer = EmployerProfileSerializer(
            profile,
            data=request.data,
            partial=True
        )
    def delete(self, request):

        profile = request.user.employer

        profile.is_active = False

        profile.save()

        return Response({
            "message": "Employer profile deactivated"
        })

        if serializer.is_valid():

            serializer.save()

            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class JobUpdateAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsEmployer
    ]

    def put(self, request, pk):

        try:
            job = Job.objects.get(
                id=pk
            )

        except Job.DoesNotExist:

            return Response(
                {
                    "error": "Job not found"
                },
                status=404
            )

        # OWNERSHIP VALIDATION
        if job.employer != request.user.employer:

            return Response(
                {
                    "error": "Not your job"
                },
                status=403
            )

        serializer = JobSerializer(
            job,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data
            )

        return Response(
            serializer.errors,
            status=400
        )
class JobStatusAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsEmployer
    ]

    def patch(self, request, pk):

        try:
            job = Job.objects.get(
                id=pk
            )

        except Job.DoesNotExist:

            return Response(
                {
                    "error": "Job not found"
                },
                status=404
            )

        # OWNERSHIP VALIDATION
        if job.employer != request.user.employer:

            return Response(
                {
                    "error": "Not your job"
                },
                status=403
            )

        status_value = request.data.get(
            "status"
        )

        if status_value not in [
            "ACTIVE",
            "CLOSED"
        ]:

            return Response(
                {
                    "error": "Invalid status"
                },
                status=400
            )

        job.status = status_value

        job.save()

        return Response({
            "message": "Job status updated",
            "status": job.status
        })

@extend_schema(
    summary="Apply to a job",
    description="Candidate applies to a specific job posting by job ID. Requires an uploaded resume on the candidate's profile.",
    examples=[
        OpenApiExample(
            'Apply request',
            value={"cover_letter": "I am excited to apply for this role..."},
            request_only=True,
        )
    ]
)
class ApplyJobAPIView(APIView):
    """Submit a job application as a candidate."""

    permission_classes = [
        IsAuthenticated,
        IsCandidate
    ]

    def post(self, request, pk):

        print("Logged in user:", request.user.username)
        print("Candidate:", request.user.candidate.id)

        try:
            job = Job.objects.get(id=pk)
        except Job.DoesNotExist:
            return Response(
                {"error": "Job not found"},
                status=404
            )

        if job.status != Job.ACTIVE:
            return Response(
                {"error": "Job is closed"},
                status=400
            )

        if Application.objects.filter(
            candidate=request.user.candidate,
            job=job
        ).exists():
            return Response(
                {"error": "Already applied"},
                status=400
            )

        resume = ""
        if request.user.candidate.resume:
            resume = str(request.user.candidate.resume)

        # --- NEW: calculate ATS score from candidate's stored skills/experience ---
        parsed_resume = {
            "skills": [
                skill.strip().lower()
                for skill in re.split(r"[,\n]+", request.user.candidate.skills or "")
                if skill.strip()
            ],
            "experience": request.user.candidate.experience or "",
            "education": [],  # candidate model may not track this separately; leave empty or adjust if it does
        }

        eligible = check_candidate_eligibility(job,parsed_resume)

        if not eligible:

            return Response(
            {
            "error": "Candidate is not eligible for this job."
            },
            status=400
    )

        ats_result = calculate_ats_score(job, parsed_resume)

        application = Application.objects.create(
            candidate=request.user.candidate,
            job=job,
            resume_snapshot=resume,
            ats_score=ats_result["score"],   # ← NEW
        )

        auto_shortlist(application)

        application.refresh_from_db()

        # Check whether this application is eligible
        # for the interview scheduling process.


        interview_ready = check_application_eligibility(application)

        if interview_ready:
            print("Application is eligible for interview scheduling.")

            interview = InterviewCall.objects.create(
            application=application,
            status=InterviewCall.QUEUED,
        )

            create_ai_interview_session(application)

            process_interview_calls.delay()
        else:
            print("Application is NOT eligible for interview scheduling.")

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

        return Response(
            serializer.data,
            status=201
        )
class ApplicationHistoryAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsCandidate
    ]

    def get(self, request):

        applications = Application.objects.filter(
            candidate=request.user.candidate
        ).select_related(
            "job"
        ).order_by(
            "-applied_at"
        )

        serializer = ApplicationSerializer(
            applications,
            many=True
        )

        return Response(
            serializer.data
        )

class AppliedJobsAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsCandidate
    ]

    def get(self, request):

        applications = Application.objects.filter(
            candidate=request.user.candidate
        ).select_related(
            "job"
        )

        jobs = []

        for application in applications:
            jobs.append(
                application.job
            )

        serializer = JobSerializer(
            jobs,
            many=True
        )

        return Response(
            serializer.data
        )

class ApplicationStatusUpdateAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsEmployer
    ]

    def patch(self, request, pk):

        try:
            application = Application.objects.select_related(
                "job",
                "candidate"
            ).get(id=pk)

        except Application.DoesNotExist:

            return Response(
                {
                    "error": "Application not found"
                },
                status=404
            )

        # Ownership validation
        if application.job.employer != request.user.employer:

            return Response(
                {
                    "error": "Not your application"
                },
                status=403
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
                {
                    "error": "Invalid status"
                },
                status=400
            )

        application.status = new_status
        application.save()

        return Response({
            "message": "Application status updated",
            "status": application.status
        })

class EmployerJobsAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsEmployer
    ]

    def get(self, request):

        jobs = Job.objects.filter(
            employer=request.user.employer
        ).order_by(
            "-created_at"
        )

        serializer = JobSerializer(
            jobs,
            many=True
        )

        return Response(
            serializer.data
        )

class ApplicantListAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsEmployer
    ]

    def get(self, request, pk):

        try:
            job = Job.objects.get(
                id=pk
            )

        except Job.DoesNotExist:

            return Response(
                {
                    "error": "Job not found"
                },
                status=404
            )

        # Ownership Validation
        if job.employer != request.user.employer:

            return Response(
                {
                    "error": "Not your job"
                },
                status=403
            )

        applications = Application.objects.filter(
            job=job
        )

        # ATS Status Filter
        status_filter = request.GET.get("status")

        if status_filter:
            applications = applications.filter(
                status=status_filter
            )

        # Candidate Search
        search = request.GET.get("search")

        if search:
            applications = applications.filter(
            candidate__user__username__icontains=search
                )

        applications = applications.select_related(
            "candidate",
            "candidate__user"
        )

        serializer = ApplicationSerializer(
            applications,
            many=True
        )

        return Response(
            serializer.data
        )

class ApplicationCountAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsEmployer
    ]

    def get(self, request, pk):

        try:
            job = Job.objects.get(
                id=pk
            )

        except Job.DoesNotExist:

            return Response(
                {
                    "error": "Job not found"
                },
                status=404
            )

        # Ownership Validation
        if job.employer != request.user.employer:

            return Response(
                {
                    "error": "Not your job"
                },
                status=403
            )

        total = Application.objects.filter(
            job=job
        ).count()

        shortlisted = Application.objects.filter(
            job=job,
            status=Application.SHORTLISTED
        ).count()

        rejected = Application.objects.filter(
            job=job,
            status=Application.REJECTED
        ).count()

        selected = Application.objects.filter(
            job=job,
            status=Application.SELECTED
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

    permission_classes = [
        IsAuthenticated,
        IsEmployer
    ]

    def get(self, request, pk):

        try:
            job = Job.objects.get(
                id=pk
            )

        except Job.DoesNotExist:

            return Response(
                {
                    "error": "Job not found"
                },
                status=404
            )

        # Ownership Validation
        if job.employer != request.user.employer:

            return Response(
                {
                    "error": "Not your job"
                },
                status=403
            )

        total = Application.objects.filter(
            job=job
        ).count()

        shortlisted = Application.objects.filter(
            job=job,
            status=Application.SHORTLISTED
        ).count()

        if total == 0:
            ratio = 0
        else:
            ratio = round((shortlisted / total) * 100, 2)

        return Response(
            {
                "job": job.title,
                "total_applications": total,
                "shortlisted": shortlisted,
                "shortlist_ratio": f"{ratio}%"
            }
        )

class SavedJobsAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsCandidate
    ]

    def get(self, request):

        saved_jobs = SavedJob.objects.filter(
            candidate=request.user.candidate
        ).select_related("job")

        serializer = SavedJobSerializer(
            saved_jobs,
            many=True
        )

        return Response(serializer.data)
class SaveJobAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsCandidate
    ]

    def post(self, request, pk):

        try:
            job = Job.objects.get(id=pk)

        except Job.DoesNotExist:
            return Response(
                {"error": "Job not found"},
                status=404
            )

        if SavedJob.objects.filter(
            candidate=request.user.candidate,
            job=job
        ).exists():

            return Response(
                {"error": "Job already saved"},
                status=400
            )

        saved_job = SavedJob.objects.create(
            candidate=request.user.candidate,
            job=job
        )

        serializer = SavedJobSerializer(saved_job)

        return Response(
            serializer.data,
            status=201
        )

class CandidateDashboardAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsCandidate
    ]

    def get(self, request):

        applied_jobs = Application.objects.filter(
            candidate=request.user.candidate
        ).count()

        saved_jobs = SavedJob.objects.filter(
            candidate=request.user.candidate
        ).count()

        return Response({
            "candidate": request.user.username,
            "applied_jobs": applied_jobs,
            "saved_jobs": saved_jobs,
        })

class ApplicationTimelineAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsCandidate
    ]

    def get(self, request):

        applications = Application.objects.filter(
            candidate=request.user.candidate
        ).select_related(
            "job"
        ).order_by(
            "-applied_at"
        )

        data = []

        for application in applications:

            data.append({
                "job": application.job.title,
                "company": application.job.employer.company_name,
                "status": application.status,
                "applied_at": application.applied_at,
                "last_updated": application.updated_at,
            })

        return Response(data)
class RecommendedJobsAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsCandidate
    ]

    def get(self, request):

        candidate = request.user.candidate

        jobs = Job.objects.filter(
            status=Job.ACTIVE
        )

        # Simple recommendation using candidate skills
        if candidate.skills:

            skills = [
                skill.strip()
                for skill in candidate.skills.split(",")
            ]

            query = Q()

            for skill in skills:
                query |= Q(skills__icontains=skill)

            jobs = jobs.filter(query)

        serializer = JobSerializer(
            jobs,
            many=True
        )

        return Response(serializer.data)

class InterviewStatusAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsCandidate
    ]

    def get(self, request):

        applications = Application.objects.filter(
            candidate=request.user.candidate
        ).select_related(
            "job"
        )

        data = []

        for application in applications:

            if application.status in [
                Application.SHORTLISTED,
                Application.INTERVIEW_SCHEDULED,
                Application.SELECTED,
            ]:

                data.append({
                    "job": application.job.title,
                    "status": application.status,
                    "updated_at": application.updated_at,
                })

        return Response(data)

class EmployerApprovalAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin
    ]

    def patch(self, request, pk):

        try:
            employer = Employer.objects.get(id=pk)

        except Employer.DoesNotExist:

            return Response(
                {
                    "error": "Employer not found"
                },
                status=404
            )

        employer.is_approved = True
        employer.save()

        return Response(
            {
                "message": "Employer approved successfully"
            }
        )

class UserBlockAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin
    ]

    def patch(self, request, pk):

        try:
            user = User.objects.get(id=pk)

        except User.DoesNotExist:

            return Response(
                {
                    "error": "User not found"
                },
                status=404
            )

        user.is_active = False
        user.save()

        return Response(
            {
                "message": "User blocked successfully"
            }
        )
class PlatformStatsAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin
    ]

    def get(self, request):

        data = {
            "total_users": User.objects.count(),
            "total_employers": Employer.objects.count(),
            "total_candidates": Candidate.objects.count(),
            "total_jobs": Job.objects.count(),
            "total_applications": Application.objects.count(),
        }

        return Response(data)

class JobActivityAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin
    ]

    def get(self, request):

        data = {
            "total_jobs": Job.objects.count(),
            "active_jobs": Job.objects.filter(status="ACTIVE").count(),
            "closed_jobs": Job.objects.filter(status="CLOSED").count(),
            "featured_jobs": Job.objects.filter(is_featured=True).count(),
        }

        return Response(data)

class RemoveSpamJobAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin
    ]

    def patch(self, request, pk):

        try:
            job = Job.objects.get(id=pk)

        except Job.DoesNotExist:

            return Response(
                {
                    "error": "Job not found"
                },
                status=404
            )

        job.status = "CLOSED"
        job.save()

        return Response(
            {
                "message": "Spam job removed successfully"
            }
        )

class AuditLogAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin
    ]

    def get(self, request):

        logs = AuditLog.objects.all().order_by("-created_at")

        serializer = AuditLogSerializer(
            logs,
            many=True
        )

        return Response(serializer.data)


@extend_schema(
    summary="Parse a resume",
    description="Uploads and parses a resume file against a specific job, extracting skills, education, experience, and an ATS match score."
)
class ResumeParserAPIView(APIView):
    """Extract structured data (skills, education, experience) from an uploaded resume and score it against a job."""

    permission_classes = [
        IsAuthenticated,
        IsCandidate,
    ]

    def post(self, request):

        uploaded_file = request.FILES.get("resume")

        if not uploaded_file:
            return Response(
                {"error": "Resume file required"},
                status=400,
            )

        job_id = request.data.get("job_id")

        if not job_id:
            return Response(
                {"error": "job_id is required"},
                status=400,
            )

        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response(
                {"error": "Job not found"},
                status=404,
            )

        clean_text = extract_resume_text(uploaded_file)

        skills = extract_skills(clean_text)
        experience = extract_experience(clean_text)
        education = extract_education(clean_text)

        parsed_resume = {
            "skills": skills,
            "experience": experience,
            "education": education,
        }

        # Job Skills
        job_skills = [
            skill.strip().lower()
            for skill in re.split(r"[,\n]+", job.skills)
            if skill.strip()
        ]

        # Resume Skills
        resume_skills = [
            skill.lower()
            for skill in skills
        ]

        # Match Skills
        matched_skills = [
            skill for skill in job_skills if skill in resume_skills
        ]

        # ATS Score
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
            status=200,
        )

class RankedCandidatesAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsEmployer,
    ]

    throttle_classes = [
        PremiumAPIRateThrottle,
    ]

    def get(self, request, pk):

        employer = request.user.employer

        if not can_view_ai_analytics(employer):
            return Response(
                {
                    "error": "Your subscription does not allow access to candidate ranking."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            job = Job.objects.get(id=pk)

        except Job.DoesNotExist:
            return Response(
                {
                    "error": "Job not found"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if job.employer != employer:
            return Response(
                {
                    "error": "Not your job"
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        applications = (
            Application.objects
            .filter(job=job)
            .select_related(
                "candidate",
                "candidate__user",
            )
            .order_by("-ats_score")
        )

        data = []

        for application in applications:
            data.append(
                {
                    "candidate": application.candidate.user.username,
                    "ats_score": application.ats_score,
                    "suitability": f"{application.ats_score}%",
                    "status": application.status,
                    "applied_at": application.applied_at,
                }
            )

        return Response(
            {
                "job": job.title,
                "total_candidates": len(data),
                "ranked_candidates": data,
            },
            status=status.HTTP_200_OK,
        )

class ProcessApplicationsAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsEmployer
    ]

    def post(self, request):

        updated = process_pending_applications()

        return Response(
            {
                "message": "Batch processing completed.",
                "processed_applications": updated,
            }
        )

class UpdateApplicationStatusAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsEmployer,
    ]

    def patch(self, request, pk):

        try:
            application = Application.objects.get(id=pk)

        except Application.DoesNotExist:

            return Response(
                {
                    "error": "Application not found"
                },
                status=404
            )

        AccessValidationService.validate_application_job_owner(

            request.user,
    application,
)

        status = request.data.get("status")

        if status not in [

            Application.SHORTLISTED,
            Application.REJECTED,

        ]:

            return Response(
                {
                    "error": "Invalid status"
                },
                status=400
            )

        application.status = status

        application.save()

        if status == Application.SHORTLISTED:

            subject, message = shortlisted_template(
                application.candidate.user.username,
                application.job.title,
            )

            send_email_task.delay(
                request.user.email,
                subject,
                message,
            )


        elif status == Application.REJECTED:

            subject, message = rejected_template(
                application.candidate.user.username,
                application.job.title,
            )

            send_email_task.delay(
                request.user.email,
                subject,
                message,
            )

        serializer = ApplicationSerializer(application)

        return Response(serializer.data)

class SubmitAnswerAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, answer_id):

        try:
            ai_answer = AIAnswer.objects.select_related(
                "question__session__interview_call__application__candidate__user"
            ).get(id=answer_id)

        except AIAnswer.DoesNotExist:
            return Response(
                {"error": "Answer not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        candidate = (
            ai_answer.question
            .session
            .interview_call
            .application
            .candidate
        )

        if request.user != candidate.user:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = SubmitAnswerSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        ai_answer.answer = serializer.validated_data["answer"]
        ai_answer.save()

        evaluator = AnswerEvaluator()
        evaluator.evaluate(ai_answer)

        AuditService().log_action(
            user=request.user,
            action="Submitted AI interview answer",
            object_type="AIAnswer",
            object_id=ai_answer.id,
        )

        return Response(
            {
                "message": "Answer submitted successfully",
                "score": ai_answer.final_score,
                "feedback": ai_answer.ai_feedback,
            }
        )

class AnswerScoreAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            answer = AIAnswer.objects.select_related(
                "question__session__interview_call__application__candidate__user"
            ).get(pk=pk)

            candidate = (
                answer.question
                .session
                .interview_call
                .application
                .candidate
            )

            if request.user != candidate.user:
                return Response(
                    {"error": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        except AIAnswer.DoesNotExist:
            return Response(
                {"error": "Answer not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            "question": answer.question.question,
            "answer": answer.answer,
            "session_id": answer.question.session.id,
            "relevance_score": answer.relevance_score,
            "completeness_score": answer.completeness_score,
            "confidence_score": answer.confidence_score,
            "final_score": answer.final_score,
            "matched_keywords": answer.matched_keywords,
            "evaluated_at": answer.evaluated_at,
            "feedback": answer.ai_feedback,
        })

class CreateAvailabilitySlotAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    def post(self, request):

        employer = request.user.employer

        data = request.data.copy()

        data["employer"] = employer.id

        serializer = AvailabilitySlotSerializer(data=data)

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

class AvailabilityListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        slots = AvailabilitySlot.objects.filter(
            is_booked=False,
        ).order_by(
            "date",
            "start_time",
        )

        serializer = AvailabilitySlotSerializer(
            slots,
            many=True,
        )

        return Response(serializer.data)

class BookInterviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        application_id = request.data.get("application_id")
        slot_id = request.data.get("slot_id")

        try:
            application = Application.objects.get(id=application_id)
            AccessValidationService.validate_application_owner(
    request.user,
    application,
)
            slot = AvailabilitySlot.objects.get(id=slot_id)
        except (Application.DoesNotExist, AvailabilitySlot.DoesNotExist):
            return Response(
                {"error": "Invalid application or slot"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if slot.is_booked:
            return Response(
                {"error": "Slot already booked"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        schedule = InterviewSchedule.objects.create(
            application=application,
            slot=slot,
            status=InterviewSchedule.SCHEDULED,
        )

        slot.is_booked = True
        slot.save()

        AuditService().log_action(
            user=request.user,
            action="Booked interview",
            object_type="InterviewSchedule",
            object_id=schedule.id,)

        return Response(
    {
        "message": "Interview booked successfully",
        "schedule_id": schedule.id,
    },
    status=status.HTTP_201_CREATED,
)

class SendInterviewRemindersAPIView(APIView):

    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):

        send_interview_reminders.delay()

        return Response(
            {
                "message": "Reminder task started"
            },
            status=status.HTTP_200_OK,
        )

class CandidateReportAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsEmployer,
    ]

    throttle_classes = [
        PremiumAPIRateThrottle,
    ]

    def get(self, request, pk):

        employer = request.user.employer

        if not can_view_ai_analytics(employer):
            return Response(
                {
                    "error": "Your subscription does not allow access to candidate reports."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            application = Application.objects.get(pk=pk)

        except Application.DoesNotExist:
            return Response(
                {
                    "error": "Application not found"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        AccessValidationService.validate_application_job_owner(
            request.user,
            application,
        )

        report = CandidateReportService().generate_report(
            application
        )

        return Response(
            report,
            status=status.HTTP_200_OK,
        )
    
@method_decorator(cache_page(60), name="dispatch")
class HiringFunnelAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsEmployer,
    ]

    throttle_classes = [
        PremiumAPIRateThrottle,
    ]

    def get(self, request):

        employer = request.user.employer

        if not can_view_analytics(employer):
            return Response(
                {
                    "error": "Your subscription does not allow access to analytics."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        data = AnalyticsService().hiring_funnel()

        return Response(data)


@method_decorator(cache_page(60), name="dispatch")
class JobPerformanceAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    throttle_classes = [
        PremiumAPIRateThrottle,
    ]

    def get(self, request):

        employer = request.user.employer

        if not can_view_analytics(employer):
            return Response(
                {
                    "error": "Your subscription does not allow access to analytics."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        data = AnalyticsService().job_performance()

        return Response(data)


@method_decorator(cache_page(60), name="dispatch")
class ConversionRatioAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    throttle_classes = [
        PremiumAPIRateThrottle,
    ]

    def get(self, request):

        employer = request.user.employer

        if not can_view_analytics(employer):
            return Response(
                {
                    "error": "Your subscription does not allow access to analytics."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        data = AnalyticsService().conversion_ratios()

        return Response(data)

class AIAnalyticsAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsEmployer,
    ]

    throttle_classes = [
        PremiumAPIRateThrottle,
    ]

    def get(self, request):

        employer = request.user.employer

        if not can_view_ai_analytics(employer):
            return Response(
                {
                    "error": "Your subscription does not allow access to AI analytics."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        data = AnalyticsService().ai_analytics(employer)

        return Response(data)

class CreatePaymentOrderAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsEmployer,
    ]

    def post(self, request):

        employer = request.user.employer

        amount = request.data.get("amount")
        currency = request.data.get("currency", "INR")

        if not amount:
            return Response(
                {
                    "error": "amount is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            data = PaymentService().create_order(
                employer=employer,
                amount=amount,
                currency=currency,
            )

            return Response(
                data,
                status=status.HTTP_201_CREATED,
            )

        except ValueError as exc:
            return Response(
                {
                    "error": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            return Response(
                {
                    "error": "Unable to create payment order."
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

class VerifyPaymentAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsEmployer,
    ]

    def post(self, request):

        employer = request.user.employer

        razorpay_order_id = request.data.get(
            "razorpay_order_id"
        )

        razorpay_payment_id = request.data.get(
            "razorpay_payment_id"
        )

        razorpay_signature = request.data.get(
            "razorpay_signature"
        )

        if not all(
            [
                razorpay_order_id,
                razorpay_payment_id,
                razorpay_signature,
            ]
        ):
            return Response(
                {
                    "error": "Payment verification fields are required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment = PaymentService().verify_payment(
                employer=employer,
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_signature=razorpay_signature,
            )

            return Response(
                {
                    "message": "Payment verified successfully.",
                    "transaction_id": payment.transaction_id,
                    "payment_id": payment.razorpay_payment_id,
                    "status": payment.status,
                },
                status=status.HTTP_200_OK,
            )

        except ValueError as exc:
            return Response(
                {
                    "error": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

class CapturePaymentAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsEmployer,
    ]

    def post(self, request):

        employer = request.user.employer

        payment_id = request.data.get(
            "razorpay_payment_id"
        )

        amount = request.data.get("amount")

        if not payment_id or not amount:
            return Response(
                {
                    "error": "razorpay_payment_id and amount are required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = PaymentService().capture_payment(
                employer=employer,
                razorpay_payment_id=payment_id,
                amount=amount,
            )

            return Response(
                {
                    "message": "Payment captured successfully.",
                    "payment": result,
                },
                status=status.HTTP_200_OK,
            )

        except ValueError as exc:
            return Response(
                {
                    "error": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            return Response(
                {
                    "error": "Unable to capture payment."
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

class RazorpayWebhookAPIView(APIView):

    permission_classes = [
        AllowAny,
    ]

    authentication_classes = []

    def post(self, request):

        signature = request.headers.get(
            "X-Razorpay-Signature"
        )

        if not signature:
            return Response(
                {
                    "error": "Webhook signature missing."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_body = request.body

        if not PaymentService().verify_webhook_signature(
            raw_body,
            signature,
        ):
            return Response(
                {
                    "error": "Invalid webhook signature."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            return Response(
                {
                    "error": "Invalid webhook payload."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        PaymentService().process_webhook_event(payload)

        return Response(
            {
                "message": "Webhook received successfully."
            },
            status=status.HTTP_200_OK,
        )

class SubscriptionStatusAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsEmployer,
    ]

    def get(self, request):

        employer = request.user.employer

        data = get_subscription_status(employer)

        return Response(
            data,
            status=status.HTTP_200_OK,
        )

class AuthTestAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        return Response({
            "message": "Authentication working",
            "user": request.user.username,
            "user_id": request.user.id,
        })

class AdminTransactionListAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]

    def get(self, request):

        transactions = (
            PaymentTransaction.objects
            .select_related(
                "employer",
                "subscription__plan",
            )
            .order_by("-created_at")
        )

        serializer = PaymentTransactionSerializer(
            transactions,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class AdminBillingHistoryAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]

    def get(self, request):

        records = (
            BillingHistory.objects
            .select_related(
                "employer",
                "subscription__plan",
                "transaction",
            )
            .order_by("-created_at")
        )

        serializer = BillingHistorySerializer(
            records,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
class DailyRevenueAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]

    def get(self, request):

        data = BillingService.daily_revenue()

        return Response(
            data,
            status=status.HTTP_200_OK,
        )


class MonthlyRevenueAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]

    def get(self, request):

        data = BillingService.monthly_revenue()

        return Response(
            data,
            status=status.HTTP_200_OK,
        )


class PlanWiseRevenueAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]

    def get(self, request):

        data = BillingService.plan_wise_revenue()

        return Response(
            data,
            status=status.HTTP_200_OK,
        )


class RevenueSummaryAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]

    def get(self, request):

        total = BillingService.total_revenue()

        return Response(
            {
                "total_revenue": total,
                "currency": "INR",
            },
            status=status.HTTP_200_OK,
        )

class AdminRefundAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]

    def post(self, request, pk):

        try:
            transaction_obj = PaymentTransaction.objects.get(
                pk=pk
            )
        except PaymentTransaction.DoesNotExist:
            return Response(
                {
                    "error": "Transaction not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        amount = request.data.get("amount")
        reason = request.data.get(
            "reason",
            "Admin initiated refund",
        )

        try:

            refund = PaymentService().refund_payment(
                transaction=transaction_obj,
                amount=amount,
                reason=reason,
            )

            refund_record = RefundRecord.objects.create(
                transaction=transaction_obj,
                employer=transaction_obj.employer,
                refund_id=refund["id"],
                amount=(
                    refund["amount"] / 100
                ),
                currency=refund.get(
                    "currency",
                    transaction_obj.currency,
                ),
                reason=reason,
                status=RefundRecord.PROCESSED,
                processed_at=timezone.now(),
            )

            transaction_obj.status = (
                PaymentTransaction.REFUNDED
            )
            transaction_obj.save(
                update_fields=["status"]
            )

            FinancialAuditLog.objects.create(
                transaction=transaction_obj,
                employer=transaction_obj.employer,
                action=(
                    FinancialAuditLog.REFUND_CREATED
                ),
                message=(
                    f"Refund {refund_record.refund_id} "
                    f"created for transaction "
                    f"{transaction_obj.transaction_id}."
                ),
                ip_address=(
                    request.META.get("REMOTE_ADDR")
                ),
            )

            return Response(
                RefundRecordSerializer(
                    refund_record
                ).data,
                status=status.HTTP_201_CREATED,
            )

        except ValueError as exc:

            return Response(
                {
                    "error": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as exc:

            FinancialAuditLog.objects.create(
                transaction=transaction_obj,
                employer=transaction_obj.employer,
                action=(
                    FinancialAuditLog.REFUND_FAILED
                ),
                message=str(exc),
                ip_address=(
                    request.META.get("REMOTE_ADDR")
                ),
            )

            return Response(
                {
                    "error": "Refund failed."
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )