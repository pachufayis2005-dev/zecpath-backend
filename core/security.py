from core.services import LoggingService


def log_unauthorized_access(request, action):
    """
    Store unauthorized access attempts.
    """

    ip = request.META.get(
        "REMOTE_ADDR",
        None,
    )

    user = None

    if request.user.is_authenticated:
        user = request.user

    LoggingService().log_security(
        user=user,
        ip_address=ip,
        action=action,
    )