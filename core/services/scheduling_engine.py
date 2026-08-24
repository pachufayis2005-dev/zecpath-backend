from django.db import transaction

from core.models import (
    AvailabilitySlot,
    InterviewSchedule,
)


class SchedulingEngine:
    """
    Handles interview scheduling.
    """

    def get_available_slots(self, employer):

        return AvailabilitySlot.objects.filter(
            employer=employer,
            is_booked=False,
        ).order_by(
            "date",
            "start_time",
        )

    @transaction.atomic
    def schedule_interview(
        self,
        application,
        slot,
    ):

        if slot.is_booked:

            raise ValueError("Slot already booked.")

        schedule = InterviewSchedule.objects.create(
            application=application,
            slot=slot,
        )

        slot.is_booked = True
        slot.save()

        return schedule
