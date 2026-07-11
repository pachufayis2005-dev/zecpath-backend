from rest_framework import serializers
from .models import Job, Application,SavedJob,AuditLog


class JobSerializer(serializers.ModelSerializer):

    class Meta:
        model = Job

        fields = [
            "id",
            "title",
            "description",
            "skills",
            "experience",
            "salary",
            "location",
            "job_type",
            "status",
            "created_at",
            "updated_at",
            "is_featured",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class ApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Application

        fields = [
            "id",
            "job",
            "resume_snapshot",
            "status",
            "applied_at",
        ]

class SavedJobSerializer(serializers.ModelSerializer):

    class Meta:
        model = SavedJob

        fields = [
            "id",
            "job",
            "saved_at",
        ]

class AuditLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = AuditLog

        fields = [
            "id",
            "admin",
            "action",
            "created_at",
        ]