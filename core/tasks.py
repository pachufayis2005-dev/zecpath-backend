from celery import shared_task

from core.services import ReminderService
from core.services.ai_bridge import AIBridgeService
from core.services_py import send_email_notification

from .models import InterviewCall, ReminderLog


@shared_task
def test_task():
    print("Celery is Working!")
    return "Success"


@shared_task
def send_email_task(recipient, subject, message):
    send_email_notification(
        recipient,
        subject,
        message,
    )
    return "Email Sent"


@shared_task
def process_interview_calls():

    queued_calls = InterviewCall.objects.filter(status=InterviewCall.QUEUED)

    ai_service = AIBridgeService()

    for interview in queued_calls:

        print(f"\nProcessing Interview #{interview.id}")

        interview.status = InterviewCall.IN_PROGRESS
        interview.save()

        success = ai_service.start_interview(interview)

        if success:
            interview.status = InterviewCall.COMPLETED
        else:
            interview.status = InterviewCall.FAILED

        interview.save()

        print(f"Interview {interview.id} -> {interview.status}")

    return "Interview Processing Finished"


@shared_task
def send_interview_reminders():

    service = ReminderService()

    interviews = service.get_upcoming_interviews()

    count = 0

    for interview in interviews:

        already_sent = ReminderLog.objects.filter(
            interview=interview,
            reminder_type=ReminderLog.DAY_BEFORE,
        ).exists()

        if already_sent:
            continue

        service.send_reminder(
            interview,
            ReminderLog.DAY_BEFORE,
        )

        count += 1

    return f"{count} reminder(s) sent."
