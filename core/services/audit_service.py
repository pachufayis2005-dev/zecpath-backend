from core.models import AuditTrail


class AuditService:
    """
    Records important user actions.
    """

    def log_action(
        self,
        user,
        action,
        object_type,
        object_id,
    ):

        AuditTrail.objects.create(
            user=user,
            action=action,
            object_type=object_type,
            object_id=object_id,
        )