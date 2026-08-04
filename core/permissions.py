from rest_framework.permissions import BasePermission
from core.services import LoggingService


class IsAdmin(BasePermission):

    def has_permission(self, request, view):
        return request.user.role == "ADMIN"

class IsEmployer(BasePermission):

    def has_permission(self, request, view):

        if request.user.role != "EMPLOYER":

            LoggingService().log_security(
                user=request.user,
                ip_address=request.META.get("REMOTE_ADDR"),
                action="Unauthorized access to Employer API",
            )

            return False

        return True

class IsCandidate(BasePermission):

    def has_permission(self, request, view):
        return request.user.role == "CANDIDATE"