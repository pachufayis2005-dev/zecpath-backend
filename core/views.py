from django.shortcuts import render

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
from .serializers import (ApplicationSerializer,SavedJobSerializer,AuditLogSerializer,)
from .models import (
    User,
    Job,
    Candidate,
    Employer,
    Application,
    SavedJob,
    AuditLog,
)
from .serializers import JobSerializer


class JobListAPIView(APIView):

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

        serializer = JobSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save(
                employer=request.user.employer
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
    
class LoginAPIView(TokenObtainPairView):
    pass

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

class ApplyJobAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsCandidate
    ]

    def post(self, request, pk):

        # Find job
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

        # Check if job is active
        if job.status != Job.ACTIVE:

            return Response(
                {
                    "error": "Job is closed"
                },
                status=400
            )

        # Duplicate prevention
        if Application.objects.filter(
            candidate=request.user.candidate,
            job=job
        ).exists():

            return Response(
                {
                    "error": "Already applied"
                },
                status=400
            )

        # Resume binding
        resume = ""

        if request.user.candidate.resume:
            resume = str(
                request.user.candidate.resume
            )

        application = Application.objects.create(
            candidate=request.user.candidate,
            job=job,
            resume_snapshot=resume
        )

        serializer = ApplicationSerializer(
            application
        )

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