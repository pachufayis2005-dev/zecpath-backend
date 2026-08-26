from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..permissions import IsCandidate, IsEmployer
from ..profile_serializers import CandidateProfileSerializer, EmployerProfileSerializer


class CandidateProfileAPIView(APIView):

    permission_classes = [IsAuthenticated, IsCandidate]

    def get(self, request):

        profile = request.user.candidate
        serializer = CandidateProfileSerializer(profile)

        return Response(serializer.data)

    def put(self, request):

        profile = request.user.candidate
        serializer = CandidateProfileSerializer(
            profile, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):

        profile = request.user.candidate
        profile.is_active = False
        profile.save()

        return Response({"message": "Candidate profile deactivated"})


class EmployerProfileAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    def get(self, request):

        profile = request.user.employer
        serializer = EmployerProfileSerializer(profile)

        return Response(serializer.data)

    def put(self, request):
        profile = request.user.employer
        serializer = EmployerProfileSerializer(
            profile,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request):
        profile = request.user.employer
        profile.is_active = False
        profile.save()

        return Response({"message": "Employer profile deactivated"})