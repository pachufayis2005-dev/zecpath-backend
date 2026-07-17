import threading

from .models import Application,EmailLog
from .utils import calculate_ats_score


def auto_shortlist(application):

    score = application.ats_score

    if score >= 80:
        application.status = Application.SHORTLISTED

    elif score < 50:
        application.status = Application.REJECTED

    else:
        application.status = Application.UNDER_REVIEW

    application.save()

    return application

def check_candidate_eligibility(job, parsed_resume):

    ats_result = calculate_ats_score(
        job,
        parsed_resume
    )

    if ats_result["score"] >= 50:

        return True

    return False

def process_pending_applications():

    pending = Application.objects.filter(
        status=Application.APPLIED
    )

    updated = 0

    for application in pending:

        auto_shortlist(application)

        updated += 1

    return updated

import random

def send_email_notification(
    recipient,
    subject,
    message,
    max_retries=3,
):
    from core.models import EmailLog

    attempt = 0
    success = False

    while attempt < max_retries and not success:
        attempt += 1
        try:
            print("=" * 50)
            print(f"Attempt {attempt}: Sending email...")
            print("To:", recipient)
            print("Subject:", subject)
            print("Message:")
            print(message)

            # Simulate a random failure (30% chance)
            # This lets us TEST the retry logic without a real email server.
            if random.random() < 0.3:
                raise Exception("Simulated email server error")

            print("EMAIL SENT SUCCESSFULLY")
            print("=" * 50)
            success = True

        except Exception as e:
            print(f"Attempt {attempt} FAILED: {e}")
            print("=" * 50)

    # After the loop, log the final result
    if success:
        EmailLog.objects.create(
            recipient=recipient,
            subject=subject,
            message=message,
            status=EmailLog.SENT,
        )
    else:
        EmailLog.objects.create(
            recipient=recipient,
            subject=subject,
            message=message,
            status=EmailLog.FAILED,
        )

    return success

def send_email_notification_async(recipient, subject, message, max_retries=3):
    thread = threading.Thread(
        target=send_email_notification,
        args=(recipient, subject, message, max_retries),
    )
    thread.start()

def application_submitted_template(
    candidate_name,
    job_title,
):

    subject = "Application Submitted Successfully"

    message = f"""
Hello {candidate_name},

Your application for the position of
'{job_title}'
has been submitted successfully.

Our recruitment team will review your profile.

Thank you for using ZecPath.

Regards,
ZecPath Team
"""

    return subject, message