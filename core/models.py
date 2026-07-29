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

    is_approved = models.BooleanField(
    default=False
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

    class Meta:

        indexes = [

            models.Index(fields=["status"]),
            models.Index(fields=["location"]),
            models.Index(fields=["job_type"]),

        ]

    def __str__(self):
        return self.title

class Application(models.Model):

    APPLIED = "APPLIED"
    UNDER_REVIEW = "UNDER_REVIEW"
    SHORTLISTED = "SHORTLISTED"
    INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED"
    REJECTED = "REJECTED"
    SELECTED = "SELECTED"

    STATUS_CHOICES = [
    (APPLIED, "Applied"),
    (UNDER_REVIEW, "Under Review"),
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

    ats_score = models.FloatField(
    default=0,
    null=True,
    blank=True,
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

    class Meta:

        indexes = [

            models.Index(fields=["candidate"]),
            models.Index(fields=["job"]),
            models.Index(fields=["status"]),

        ]

    def __str__(self):
        return (
            f"{self.candidate.user.username}"
            f" -> "
            f"{self.job.title}"
        )

class InterviewCall(models.Model):

    QUEUED = "QUEUED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

    STATUS_CHOICES = [
        (QUEUED, "Queued"),
        (IN_PROGRESS, "In Progress"),
        (COMPLETED, "Completed"),
        (FAILED, "Failed"),
    ]

    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name="interview_call",
    )

    scheduled_time = models.DateTimeField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=QUEUED,
    )

    retry_count = models.IntegerField(
        default=0,
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.application} - {self.status}"

class AIInterviewSession(models.Model):

    STARTED = "STARTED"
    COMPLETED = "COMPLETED"

    STATUS_CHOICES = [
        (STARTED, "Started"),
        (COMPLETED, "Completed"),
    ]

    interview_call = models.OneToOneField(
        InterviewCall,
        on_delete=models.CASCADE,
    )

    started_at = models.DateTimeField(
        auto_now_add=True
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STARTED,
    )

    def __str__(self):
        return f"Session {self.id}"

class AIQuestion(models.Model):

    INTRODUCTION = "INTRODUCTION"
    EXPERIENCE = "EXPERIENCE"
    SKILLS = "SKILLS"
    AVAILABILITY = "AVAILABILITY"
    SALARY = "SALARY"

    CATEGORY_CHOICES = [
        (INTRODUCTION, "Introduction"),
        (EXPERIENCE, "Experience"),
        (SKILLS, "Skills"),
        (AVAILABILITY, "Availability"),
        (SALARY, "Salary"),
    ]

    session = models.ForeignKey(
        AIInterviewSession,
        on_delete=models.CASCADE,
        related_name="questions",
    )

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
    )

    question = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.category} - {self.question[:40]}"

class AIAnswer(models.Model):

    question = models.OneToOneField(
        AIQuestion,
        on_delete=models.CASCADE,
    )

    answer = models.TextField()

    transcript = models.JSONField(
        default=dict,
    )

    confidence_score = models.FloatField(
        default=0,
    )

    relevance_score = models.FloatField(
        default=0,
    )

    completeness_score = models.FloatField(
        default=0,
    )

    final_score = models.FloatField(
        default=0,
    )

    ai_feedback = models.TextField(
        blank=True,
    )

    matched_keywords = models.JSONField(
        default=list,
    )

    evaluated_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return self.answer[:40]

class CallLog(models.Model):

    session = models.ForeignKey(
        AIInterviewSession,
        on_delete=models.CASCADE,
    )

    triggered_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

    action = models.CharField(
        max_length=200,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return self.action

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

class AuditLog(models.Model):

    admin = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    action = models.CharField(
        max_length=255
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.action

class EmailLog(models.Model):

    recipient = models.EmailField()

    subject = models.CharField(
        max_length=255
    )

    message = models.TextField()

    SENT = "SENT"
    FAILED = "FAILED"

    STATUS_CHOICES = [
    (SENT, "Sent"),
    (FAILED, "Failed"),
    ]

    status = models.CharField(
    max_length=20,
    choices=STATUS_CHOICES,
    default=SENT
    )

    sent_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.subject

class AvailabilitySlot(models.Model):

    employer = models.ForeignKey(
        Employer,
        on_delete=models.CASCADE,
        related_name="availability_slots",
    )

    date = models.DateField()

    start_time = models.TimeField()

    end_time = models.TimeField()

    is_booked = models.BooleanField(
        default=False
    )

    def __str__(self):

        return (
            f"{self.employer.user.username} "
            f"{self.date} "
            f"{self.start_time}"
        )


class InterviewSchedule(models.Model):

    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

    STATUS_CHOICES = [

        (SCHEDULED, "Scheduled"),
        (COMPLETED, "Completed"),
        (CANCELLED, "Cancelled"),
    ]

    application = models.OneToOneField(

        Application,

        on_delete=models.CASCADE,

        related_name="schedule",
    )

    slot = models.OneToOneField(

        AvailabilitySlot,

        on_delete=models.CASCADE,

        related_name="interview",
    )

    scheduled_at = models.DateTimeField(

        auto_now_add=True
    )

    status = models.CharField(

        max_length=20,

        choices=STATUS_CHOICES,

        default=SCHEDULED,
    )

    def __str__(self):

        return (
            f"{self.application.id} - "
            f"{self.status}"
        )
