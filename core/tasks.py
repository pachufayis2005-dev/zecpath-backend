from celery import shared_task

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