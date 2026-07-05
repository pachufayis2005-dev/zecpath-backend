from rest_framework import serializers
from .models import Job


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