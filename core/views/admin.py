from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import AuditLog, Candidate, Employer, Job, User, Application
from ..permissions import IsAdmin
from ..serializers import AuditLogSerializer


class AdminAPIView(APIView):

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        return Response({"message": "Admin Access Granted"})


class EmployerApprovalAPIView(APIView):

    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, pk):

        employer = get_object_or_404(Employer, id=pk)

        employer.is_approved = True
        employer.save()

        return Response({"message": "Employer approved successfully"})


class UserBlockAPIView(APIView):

    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, pk):

        user = get_object_or_404(User, id=pk)

        user.is_active = False
        user.save()

        return Response({"message": "User blocked successfully"})


class PlatformStatsAPIView(APIView):

    permission_classes = [IsAuthenticated, IsAdmin]

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

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):

        data = {
            "total_jobs": Job.objects.count(),
            "active_jobs": Job.objects.filter(status="ACTIVE").count(),
            "closed_jobs": Job.objects.filter(status="CLOSED").count(),
            "featured_jobs": Job.objects.filter(is_featured=True).count(),
        }

        return Response(data)


class RemoveSpamJobAPIView(APIView):

    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, pk):

        job = get_object_or_404(Job, id=pk)

        job.status = "CLOSED"
        job.save()

        return Response({"message": "Spam job removed successfully"})


class AuditLogAPIView(APIView):

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):

        logs = AuditLog.objects.all().order_by("-created_at")

        serializer = AuditLogSerializer(logs, many=True)

        return Response(serializer.data)