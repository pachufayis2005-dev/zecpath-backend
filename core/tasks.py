from celery import shared_task
import random
import time

from .models import InterviewCall

from core.services import send_email_notification


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

    for interview in queued_calls:

        print(f"Processing Interview #{interview.id}")

        interview.status = InterviewCall.IN_PROGRESS
        interview.save()

        # simulate recruiter making the call
        time.sleep(2)

        if random.random() < 0.8:
            interview.status = InterviewCall.COMPLETED
        else:
            interview.status = InterviewCall.FAILED

        interview.save()

        print(
            f"Interview {interview.id} -> {interview.status}"
        )

    return "Interview Processing Finished"