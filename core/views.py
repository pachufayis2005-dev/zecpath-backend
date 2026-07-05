from django.shortcuts import render

from .pagination import JobPagination
from .profile_serializers import (CandidateProfileSerializer,EmployerProfileSerializer,)
from .permissions import IsCandidate, IsEmployer, IsAdmin
from .models import Candidate, Employer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .auth_serializers import SignupSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import Job
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