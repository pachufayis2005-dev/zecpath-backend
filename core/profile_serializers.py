from rest_framework import serializers
from .models import Candidate, Employer


class CandidateProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Candidate
        fields = [
            "id",
            "skills",
            "education",
            "experience",
            "expected_salary",
            "is_active",
        ]


class EmployerProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Employer
        fields = [
            "id",
            "company_name",
            "domain",
            "company_size",
            "is_verified",
            "is_active",
        ]