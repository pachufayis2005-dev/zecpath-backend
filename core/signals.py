from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Candidate, Employer, SubscriptionPlan, User, UserSubscription


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):

    if created:

        if instance.role == User.CANDIDATE:

            Candidate.objects.create(user=instance, skills="")

        elif instance.role == User.EMPLOYER:

            Employer.objects.create(user=instance, company_name="")


@receiver(post_save, sender=Employer)
def assign_free_subscription(sender, instance, created, **kwargs):
    """
    Automatically give every newly created Employer an ACTIVE
    FREE plan subscription, so they can immediately use limited
    features (e.g. post a limited number of jobs) without needing
    to pay first.
    """

    if not created:
        return

    if UserSubscription.objects.filter(employer=instance).exists():
        return

    free_plan, _ = SubscriptionPlan.objects.get_or_create(
        name=SubscriptionPlan.FREE,
        defaults={
            "description": "Default free plan assigned on signup.",
            "price": 0,
            "job_post_limit": 3,
            "ai_interview_limit": 5,
            "analytics_enabled": False,
            "ai_analytics_enabled": False,
            "is_active": True,
        },
    )

    UserSubscription.objects.create(
        employer=instance,
        plan=free_plan,
        status=UserSubscription.ACTIVE,
        started_at=timezone.now(),
    )