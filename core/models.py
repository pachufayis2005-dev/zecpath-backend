from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):

    ADMIN = "ADMIN"
    EMPLOYER = "EMPLOYER"
    CANDIDATE = "CANDIDATE"

    ROLE_CHOICES = [
        (ADMIN, "Admin"),
        (EMPLOYER, "Employer"),
        (CANDIDATE, "Candidate"),
    ]

    email = models.EmailField(
        unique=True
    )

    phone = models.CharField(
        max_length=20,
        blank=True
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    is_verified = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.username


class Employer(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    company_name = models.CharField(max_length=200)

    def __str__(self):
        return self.company_name


class Candidate(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    skills = models.TextField()

    def __str__(self):
        return self.user.username


class Job(models.Model):

    employer = models.ForeignKey(
        Employer,
        on_delete=models.CASCADE
    )

    title = models.CharField(max_length=200)

    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Application(models.Model):

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE
    )

    applied_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.candidate} - {self.job}"