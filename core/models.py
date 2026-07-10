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

    company_name = models.CharField(
        max_length=200
    )

    domain = models.CharField(
        max_length=200,
        blank=True
    )

    company_size = models.IntegerField(
        default=0
    )

    is_verified = models.BooleanField(
        default=False
    )

    is_active = models.BooleanField(
        default=True
    )

    def __str__(self):
        return self.company_name

class Candidate(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    skills = models.TextField()

    education = models.CharField(
        max_length=200,
        blank=True
    )

    experience = models.CharField(
        max_length=200,
        blank=True
    )

    expected_salary = models.IntegerField(
        default=0
    )

    resume = models.FileField(
        upload_to='resumes/',
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    def __str__(self):
        return self.user.username
    
class Job(models.Model):

    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"

    STATUS_CHOICES = [
        (ACTIVE, "Active"),
        (CLOSED, "Closed"),
    ]

    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    INTERNSHIP = "INTERNSHIP"
    CONTRACT = "CONTRACT"

    JOB_TYPE_CHOICES = [
        (FULL_TIME, "Full Time"),
        (PART_TIME, "Part Time"),
        (INTERNSHIP, "Internship"),
        (CONTRACT, "Contract"),
    ]

    employer = models.ForeignKey(
        Employer,
        on_delete=models.CASCADE
    )

    title = models.CharField(
        max_length=200,
        db_index=True
    )

    description = models.TextField()

    skills = models.TextField(
        blank=True
    )

    experience = models.CharField(
        max_length=100,
        blank=True
    )

    salary = models.IntegerField(
        default=0
    )

    location = models.CharField(
        max_length=200,
        blank=True
    )

    job_type = models.CharField(
        max_length=20,
        choices=JOB_TYPE_CHOICES,
        default=FULL_TIME
    )


    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=ACTIVE
    )

    is_featured = models.BooleanField(
        default=False
    )
    

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.title

class Application(models.Model):

    APPLIED = "APPLIED"
    SHORTLISTED = "SHORTLISTED"
    INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED"
    REJECTED = "REJECTED"
    SELECTED = "SELECTED"

    STATUS_CHOICES = [
    (APPLIED, "Applied"),
    (SHORTLISTED, "Shortlisted"),
    (INTERVIEW_SCHEDULED, "Interview Scheduled"),
    (REJECTED, "Rejected"),
    (SELECTED, "Selected"),
]
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE
    )

    resume_snapshot = models.TextField(
        blank=True
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=APPLIED
    )

    applied_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
    auto_now=True
    )

    status_updated_at = models.DateTimeField(
    auto_now=True
    )

    def __str__(self):
        return (
            f"{self.candidate.user.username}"
            f" -> "
            f"{self.job.title}"
        )

class SavedJob(models.Model):

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE
    )

    saved_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.candidate.user.username}"
            f" saved "
            f"{self.job.title}"
        )
