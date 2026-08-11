import hmac
import hashlib
import uuid
from decimal import Decimal

import razorpay

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from core.models import PaymentTransaction


class PaymentService:
    """
    Handles Razorpay payment operations.
    """

    def __init__(self):
        self.client = razorpay.Client(
            auth=(
                settings.RAZORPAY_KEY_ID,
                settings.RAZORPAY_KEY_SECRET,
            )
        )

    @transaction.atomic
    def create_order(
        self,
        employer,
        amount,
        currency="INR",
        subscription=None,
    ):
        amount = Decimal(str(amount))

        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")

        amount_paise = int(amount * 100)

        receipt = f"receipt_{uuid.uuid4().hex[:20]}"

        order = self.client.order.create(
            data={
                "amount": amount_paise,
                "currency": currency,
                "receipt": receipt,
                "capture": "manual",
            }
        )

        payment_transaction = PaymentTransaction.objects.create(
            employer=employer,
            subscription=subscription,
            amount=amount,
            currency=currency,
            transaction_id=order["id"],
            razorpay_order_id=order["id"],
            status=PaymentTransaction.PENDING,
        )

        return {
            "transaction_id": payment_transaction.transaction_id,
            "razorpay_order_id": order["id"],
            "amount": amount,
            "amount_paise": amount_paise,
            "currency": currency,
            "status": payment_transaction.status,
            "key_id": settings.RAZORPAY_KEY_ID,
        }

    def verify_payment(
        self,
        employer,
        razorpay_order_id,
        razorpay_payment_id,
        razorpay_signature,
    ):
        payment = PaymentTransaction.objects.filter(
            employer=employer,
            razorpay_order_id=razorpay_order_id,
        ).first()

        if not payment:
            raise ValueError("Payment transaction not found.")

        if payment.razorpay_payment_id:
            if payment.razorpay_payment_id == razorpay_payment_id:
                return payment
            raise ValueError("Payment has already been processed.")

        generated_signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(
            generated_signature,
            razorpay_signature,
        ):
            payment.status = PaymentTransaction.FAILED
            payment.save(update_fields=["status"])
            raise ValueError("Invalid payment signature.")

        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.save(
            update_fields=[
            "razorpay_payment_id",
            "razorpay_signature",
    ]
)

        payment.save(
            update_fields=[
                "razorpay_payment_id",
                "razorpay_signature",
                "status",
                "paid_at",
            ]
        )

        return payment

    def capture_payment(
        self,
        employer,
        razorpay_payment_id,
        amount,
    ):
        payment = PaymentTransaction.objects.filter(
            employer=employer,
            razorpay_payment_id=razorpay_payment_id,
        ).first()

        if not payment:
            raise ValueError("Payment transaction not found.")

        amount_paise = int(Decimal(str(amount)) * 100)

        result = self.client.payment.capture(
            razorpay_payment_id,
            amount_paise,
            {
                "currency": payment.currency,
            },
        )

        payment.status = PaymentTransaction.SUCCESS
        payment.paid_at = timezone.now()
        payment.save(
            update_fields=[
                "status",
                "paid_at",
            ]
        )

        return result

    def verify_webhook_signature(
        self,
        payload,
        signature,
    ):
        expected_signature = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(
            expected_signature,
            signature,
        )

    def process_webhook_event(self, payload):
        event = payload.get("event")

        payment_entity = (
            payload
            .get("payload", {})
            .get("payment", {})
            .get("entity", {})
        )

        refund_entity = (
            payload
            .get("payload", {})
            .get("refund", {})
            .get("entity", {})
        )

        if event in [
            "payment.captured",
            "payment.failed",
        ]:
            payment_id = payment_entity.get("id")

            payment = PaymentTransaction.objects.filter(
                razorpay_payment_id=payment_id
            ).first()

            if payment:
                if event == "payment.captured":
                    payment.status = PaymentTransaction.SUCCESS
                    payment.paid_at = timezone.now()

                    payment.save(
                        update_fields=[
                            "status",
                            "paid_at",
                        ]
                    )

                elif event == "payment.failed":
                    payment.status = PaymentTransaction.FAILED

                    payment.save(
                        update_fields=[
                            "status",
                        ]
                    )

        elif event in [
            "refund.created",
            "refund.processed",
            "refund.failed",
        ]:
            payment_id = refund_entity.get("payment_id")

            payment = PaymentTransaction.objects.filter(
                razorpay_payment_id=payment_id
            ).first()

            if payment:
                if event == "refund.processed":
                    payment.status = PaymentTransaction.REFUNDED

                    payment.save(
                        update_fields=[
                            "status",
                        ]
                    )

                elif event == "refund.failed":
                    payment.status = PaymentTransaction.SUCCESS

                    payment.save(
                        update_fields=[
                            "status",
                        ]
                    )