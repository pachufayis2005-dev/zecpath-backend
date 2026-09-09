import logging

from django.utils import timezone

from core.models import (
    InterviewSchedule,
    ReminderLog,
)
from core.services.application_service import (
    interview_day_before_template,
    interview_hour_before_template,
)

logger = logging.getLogger(__name__)


class ReminderService:

    def get_upcoming_interviews(self):

        return InterviewSchedule.objects.filter(status=InterviewSchedule.SCHEDULED)

    def send_reminder(
        self,
        interview,
        reminder_type,
    ):

        application = interview.application

        candidate = application.candidate

        job = application.job

        if reminder_type == ReminderLog.DAY_BEFORE:

            subject, message = interview_day_before_template(
                candidate.user.username,
                job.title,
                interview.slot.date,
                interview.slot.start_time,
            )

        else:

            subject, message = interview_hour_before_template(
                candidate.user.username,
                job.title,
                interview.slot.start_time,
            )

        logger.info(
            "Sending reminder email | Interview ID: %s | Subject: %s",
            interview.id,
            subject,
        )

        ReminderLog.objects.create(
            interview=interview,
            reminder_type=reminder_type,
            sent=True,
            sent_at=timezone.now(),
        )

        return True