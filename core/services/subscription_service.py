from datetime import timedelta

from django.utils import timezone

from core.models import (
    InterviewCall,
    Job,
    UserSubscription,
)

GRACE_PERIOD_DAYS = 3


def get_active_subscription(employer):
    """
    Return the employer's currently usable subscription.

    A subscription remains usable during the grace period
    after its expiry date.

    After the grace period ends, the subscription is automatically
    marked as EXPIRED.
    """

    now = timezone.now()

    subscription = (
        UserSubscription.objects.filter(
            employer=employer,
            status=UserSubscription.ACTIVE,
            plan__is_active=True,
        )
        .select_related("plan")
        .order_by("-created_at")
        .first()
    )

    if not subscription:
        return None

    # Subscription has no expiry date.
    if subscription.expires_at is None:
        return subscription

    # Subscription is still within its normal period.
    if subscription.expires_at > now:
        return subscription

    # Subscription has expired.
    # Give the employer a 3-day grace period.
    grace_period_end = subscription.expires_at + timedelta(days=GRACE_PERIOD_DAYS)

    # Still inside grace period.
    if now < grace_period_end:
        return subscription

    # Grace period has ended.
    subscription.status = UserSubscription.EXPIRED
    subscription.save(update_fields=["status", "updated_at"])

    return None


def can_post_job(employer):
    """
    Check whether the employer can create another job.

    job_post_limit = 0 means unlimited.
    """

    subscription = get_active_subscription(employer)

    if not subscription:
        return False

    limit = subscription.plan.job_post_limit

    if limit == 0:
        return True

    current_job_count = Job.objects.filter(employer=employer).count()

    return current_job_count < limit


def can_use_ai_interview(employer):
    """
    Check whether the employer can use AI interviews.

    ai_interview_limit = 0 means unlimited.
    """

    subscription = get_active_subscription(employer)

    if not subscription:
        return False

    limit = subscription.plan.ai_interview_limit

    if limit == 0:
        return True

    current_interview_count = InterviewCall.objects.filter(
        application__job__employer=employer
    ).count()

    return current_interview_count < limit


def can_view_analytics(employer):
    subscription = get_active_subscription(employer)

    if not subscription:
        return False

    return subscription.plan.analytics_enabled


def can_view_ai_analytics(employer):
    subscription = get_active_subscription(employer)

    if not subscription:
        return False

    return subscription.plan.ai_analytics_enabled


def get_subscription_status(employer):
    """
    Return the employer's subscription status and feature access.
    """

    subscription = get_active_subscription(employer)

    if not subscription:
        return {
            "active": False,
            "status": "EXPIRED_OR_NONE",
            "plan": None,
            "expires_at": None,
            "features": {
                "job_posting": False,
                "analytics": False,
                "ai_analytics": False,
                "ai_interview": False,
                "candidate_access": False,
            },
            "limits": {
                "job_post_limit": 0,
                "ai_interview_limit": 0,
                "candidate_access_limit": 0,
            },
        }

    plan = subscription.plan

    return {
        "active": True,
        "status": subscription.status,
        "plan": plan.name,
        "expires_at": subscription.expires_at,
        "features": {
            "job_posting": True,
            "analytics": plan.analytics_enabled,
            "ai_analytics": plan.ai_analytics_enabled,
            "ai_interview": True,
            "candidate_access": True,
        },
        "limits": {
            "job_post_limit": plan.job_post_limit,
            "ai_interview_limit": plan.ai_interview_limit,
            "candidate_access_limit": 0,
        },
    }