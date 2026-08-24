from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Candidate, Employer, User


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):

    if created:

        if instance.role == User.CANDIDATE:

            Candidate.objects.create(user=instance, skills="")

        elif instance.role == User.EMPLOYER:

            Employer.objects.create(user=instance, company_name="")
