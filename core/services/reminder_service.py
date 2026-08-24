from django.utils import timezone

from core.models import (
    InterviewSchedule,
    ReminderLog,
)
from core.services_py import (
    interview_day_before_template,
    interview_hour_before_template,
)


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

        print("=" * 50)
        print("Reminder Email")
        print(subject)
        print(message)
        print("=" * 50)

        ReminderLog.objects.create(
            interview=interview,
            reminder_type=reminder_type,
            sent=True,
            sent_at=timezone.now(),
        )

        return True