from celery import shared_task

from .models import InterviewCall
from core.services.ai_bridge import AIBridgeService
from core.services_py import send_email_notification


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

    queued_calls = InterviewCall.objects.filter(
        status=InterviewCall.QUEUED
    )

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

        print(
            f"Interview {interview.id} -> {interview.status}"
        )

    return "Interview Processing Finished"