from rest_framework import serializers
from .models import Candidate, Employer


class CandidateProfileSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = Candidate
        fields = '__all__'

    def validate_resume(self, value):

        if not value:
            return value

        allowed_extensions = [
            '.pdf',
            '.doc',
            '.docx'
        ]

        file_name = value.name.lower()

        if not any(
            file_name.endswith(ext)
            for ext in allowed_extensions
        ):
            raise serializers.ValidationError(
                "Only PDF, DOC and DOCX files are allowed."
            )

        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "File size cannot exceed 5MB."
            )

        return value

    def update(
        self,
        instance,
        validated_data
    ):

        new_resume = validated_data.get(
            'resume'
        )

        if new_resume and instance.resume:

            instance.resume.delete(
                save=False
            )

        return super().update(
            instance,
            validated_data
        )

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