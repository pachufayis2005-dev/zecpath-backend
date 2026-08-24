from rest_framework.exceptions import PermissionDenied

from core.models import SecurityLog


class AccessValidationService:

    @staticmethod
    def validate_application_job_owner(user, application):

        if application.job.employer.user != user:

            SecurityLog.objects.create(
                user=user,
                action="Unauthorized application access",
                ip_address="127.0.0.1",
            )

            raise PermissionDenied("You cannot access this application.")

    @staticmethod
    def validate_application_owner(user, application):

        if application.candidate.user != user:

            SecurityLog.objects.create(
                user=user,
                action="Unauthorized application access",
                ip_address="127.0.0.1",
            )

            raise PermissionDenied("You do not own this application.")
