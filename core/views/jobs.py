from datetime import datetime

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Job
from ..pagination import JobPagination
from ..permissions import IsCandidate, IsEmployer
from ..serializers import JobSerializer
from ..services.subscription_service import can_post_job
from .helpers import validate_job_owner


@extend_schema(
    summary="List all job postings",
    description="Returns a list of active job postings available on the platform.",
)
class JobListAPIView(APIView):
    """Get a list of all active jobs."""

    permission_classes = [AllowAny]

    def get(self, request):

        jobs = Job.objects.select_related("employer").all().order_by("-created_at")

        search = request.GET.get("search")
        if search:
            jobs = jobs.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(skills__icontains=search)
            )

        skill = request.GET.get("skill")
        if skill:
            jobs = jobs.filter(skills__icontains=skill)

        experience = request.GET.get("experience")
        if experience:
            jobs = jobs.filter(experience__icontains=experience)

        salary = request.GET.get("salary")
        if salary:
            if salary.lstrip("-").isdigit():
                jobs = jobs.filter(salary__gte=salary)
            else:
                return Response(
                    {"error": "salary must be a number"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        location = request.GET.get("location")
        if location:
            jobs = jobs.filter(location__icontains=location)

        job_type = request.GET.get("job_type")
        if job_type:
            jobs = jobs.filter(job_type=job_type)

        status_filter = request.GET.get("status")
        if status_filter:
            jobs = jobs.filter(status=status_filter)

        date_filter = request.GET.get("date")
        if date_filter:
            try:
                datetime.strptime(date_filter, "%Y-%m-%d")
            except ValueError:
                return Response(
                    {"error": "date must be in YYYY-MM-DD format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            jobs = jobs.filter(created_at__date=date_filter)

        paginator = JobPagination()
        paginated_jobs = paginator.paginate_queryset(jobs, request)
        serializer = JobSerializer(paginated_jobs, many=True)

        return paginator.get_paginated_response(serializer.data)


class JobCreateAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    def post(self, request):

        employer = request.user.employer

        if not can_post_job(employer):
            return Response(
                {"error": "Your subscription does not allow you to post another job."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = JobSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(employer=employer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FeaturedJobAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):


        jobs = Job.objects.filter(status=Job.ACTIVE, is_featured=True).order_by(
            "-created_at"
        )

        serializer = JobSerializer(jobs, many=True)

        return Response(serializer.data)

class LatestJobAPIView(APIView):

    permission_classes = [AllowAny]

    @method_decorator(cache_page(60 * 5))
    def get(self, request):

        jobs = Job.objects.filter(status=Job.ACTIVE).order_by("-created_at")[:5]

        serializer = JobSerializer(jobs, many=True)

        return Response(serializer.data)


class JobUpdateAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    def put(self, request, pk):

        job = get_object_or_404(Job, id=pk)

        validate_job_owner(request.user, job)

        serializer = JobSerializer(job, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JobStatusAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    def patch(self, request, pk):

        job = get_object_or_404(Job, id=pk)

        validate_job_owner(request.user, job)

        status_value = request.data.get("status")

        if status_value not in ["ACTIVE", "CLOSED"]:
            return Response(
                {"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST
            )

        job.status = status_value
        job.save()

        return Response({"message": "Job status updated", "status": job.status})


class EmployerJobsAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    def get(self, request):

        jobs = Job.objects.filter(employer=request.user.employer).order_by(
            "-created_at"
        )

        serializer = JobSerializer(jobs, many=True)

        return Response(serializer.data)


class RecommendedJobsAPIView(APIView):

    permission_classes = [IsAuthenticated, IsCandidate]

    def get(self, request):

        candidate = request.user.candidate

        jobs = Job.objects.filter(status=Job.ACTIVE)

        if candidate.skills:

            skills = [skill.strip() for skill in candidate.skills.split(",")]

            query = Q()
            for skill in skills:
                query |= Q(skills__icontains=skill)

            jobs = jobs.filter(query)

        serializer = JobSerializer(jobs, many=True)

        return Response(serializer.data)