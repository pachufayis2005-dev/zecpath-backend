from django.shortcuts import render

from .profile_serializers import (CandidateProfileSerializer,EmployerProfileSerializer,)
from .permissions import IsCandidate, IsEmployer, IsAdmin
from .models import Candidate, Employer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .auth_serializers import SignupSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated

from .models import Job
from .serializers import JobSerializer


class JobListAPIView(APIView):

    def get(self, request):

        jobs = Job.objects.all()

        serializer = JobSerializer(
            jobs,
            many=True
        )

        return Response(serializer.data)


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