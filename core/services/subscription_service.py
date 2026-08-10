from django.utils import timezone
from django.db import models

from core.models import UserSubscription


def get_active_subscription(employer):
    """
    Return the employer's currently active subscription.

    Returns None when the employer does not have a valid
    active subscription.
    """

    now = timezone.now()

    subscription = (
        UserSubscription.objects
        .filter(
            employer=employer,
            status=UserSubscription.ACTIVE,
            plan__is_active=True,
        )
        .filter(
            models.Q(expires_at__isnull=True) |
            models.Q(expires_at__gt=now)
        )
        .select_related("plan")
        .order_by("-created_at")
        .first()
    )

    return subscription


def can_post_job(employer):
    """
    Check whether the employer can create another job.

    A job_post_limit of 0 represents unlimited job posting.
    """

    subscription = get_active_subscription(employer)

    if not subscription:
        return False

    limit = subscription.plan.job_post_limit

    if limit == 0:
        return True

    from core.models import Job

    current_job_count = Job.objects.filter(
        employer=employer
    ).count()

    return current_job_count < limit


def can_use_ai_interview(employer):
    """
    Check whether the employer has access to AI interviews.

    An ai_interview_limit of 0 represents unlimited access.
    """

    subscription = get_active_subscription(employer)

    if not subscription:
        return False

    limit = subscription.plan.ai_interview_limit

    if limit == 0:
        return True

    from core.models import InterviewCall

    current_interview_count = InterviewCall.objects.filter(
        application__job__employer=employer
    ).count()

    return current_interview_count < limit


def can_view_analytics(employer):
    """
    Check whether recruiter analytics are available.
    """

    subscription = get_active_subscription(employer)

    if not subscription:
        return False

    return subscription.plan.analytics_enabled


def can_view_ai_analytics(employer):
    """
    Check whether AI-powered analytics are available.
    """

    subscription = get_active_subscription(employer)

    if not subscription:
        return False

    return subscription.plan.ai_analytics_enabled