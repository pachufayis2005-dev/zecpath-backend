from core.models import (
    AIEventLog,
    ApplicationLog,
    SecurityLog,
)


class LoggingService:
    """
    Centralized logging service.
    """

    def log_info(self, message):

        ApplicationLog.objects.create(
            level=ApplicationLog.INFO,
            message=message,
        )

    def log_warning(self, message):

        ApplicationLog.objects.create(
            level=ApplicationLog.WARNING,
            message=message,
        )

    def log_error(self, message):

        ApplicationLog.objects.create(
            level=ApplicationLog.ERROR,
            message=message,
        )

    def log_security(
        self,
        user,
        ip_address,
        action,
    ):

        SecurityLog.objects.create(
            user=user,
            ip_address=ip_address,
            action=action,
        )

    def log_ai_event(
        self,
        interview,
        event,
    ):

        AIEventLog.objects.create(
            interview=interview,
            event=event,
        )
