import uuid

from django.db.models import Sum
from django.db.models.functions import TruncMonth

from core.models import (
    BillingHistory,
    PaymentTransaction,
)


class BillingService:

    @staticmethod
    def create_billing_history(payment):
        """
        Creates a billing-history record for a successful payment.

        Returns the existing billing record if this payment
        has already been recorded.
        """

        if payment.status != PaymentTransaction.SUCCESS:
            raise ValueError(
                "Billing history can only be created " "for successful payments."
            )

        existing_record = BillingHistory.objects.filter(transaction=payment).first()

        if existing_record:
            return existing_record

        invoice_number = f"INV-{uuid.uuid4().hex[:20].upper()}"

        billing_record = BillingHistory.objects.create(
            employer=payment.employer,
            subscription=payment.subscription,
            transaction=payment,
            amount=payment.amount,
            currency=payment.currency,
            billing_period_start=(payment.paid_at),
            billing_period_end=None,
            invoice_number=invoice_number,
            status=BillingHistory.PAID,
        )

        return billing_record

    @staticmethod
    def daily_revenue():

        data = (
            PaymentTransaction.objects.filter(status=PaymentTransaction.SUCCESS)
            .values("paid_at__date")
            .annotate(revenue=Sum("amount"))
            .order_by("paid_at__date")
        )

        return [
            {
                "date": row["paid_at__date"],
                "revenue": row["revenue"],
            }
            for row in data
        ]

    @staticmethod
    def monthly_revenue():

        data = (
            PaymentTransaction.objects.filter(status=PaymentTransaction.SUCCESS)
            .annotate(month=TruncMonth("paid_at"))
            .values("month")
            .annotate(revenue=Sum("amount"))
            .order_by("month")
        )

        return [
            {
                "month": row["month"],
                "revenue": row["revenue"],
            }
            for row in data
        ]

    @staticmethod
    def plan_wise_revenue():

        data = (
            PaymentTransaction.objects.filter(
                status=PaymentTransaction.SUCCESS,
                subscription__isnull=False,
            )
            .values("subscription__plan__name")
            .annotate(revenue=Sum("amount"))
            .order_by("-revenue")
        )

        return [
            {
                "plan": row["subscription__plan__name"],
                "revenue": row["revenue"],
            }
            for row in data
        ]

    @staticmethod
    def total_revenue():

        return (
            PaymentTransaction.objects.filter(status=PaymentTransaction.SUCCESS)
            .aggregate(total=Sum("amount"))
            .get("total")
            or 0
        )
