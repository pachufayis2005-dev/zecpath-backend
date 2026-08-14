import hmac
import hashlib
import uuid
from decimal import Decimal

import razorpay

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from core.models import (
    PaymentTransaction,
    BillingHistory,
    FinancialAuditLog,
)

from core.services.financial_security_service import (
    FinancialSecurityService,
)


class PaymentService:
    """
    Handles payment operations, payment verification,
    payment capture, webhook processing and refunds.
    """

    def __init__(self):
        self.client = razorpay.Client(
            auth=(
                settings.RAZORPAY_KEY_ID,
                settings.RAZORPAY_KEY_SECRET,
            )
        )

    # ---------------------------------------------------------
    # INTERNAL BILLING HISTORY HELPER
    # ---------------------------------------------------------

    @staticmethod
    def _create_billing_history(payment):
        """
        Creates a BillingHistory record for a successful payment.

        Prevents duplicate billing history records if the same
        payment is processed more than once.
        """

        existing_record = (
            BillingHistory.objects
            .filter(transaction=payment)
            .first()
        )

        if existing_record:
            return existing_record

        now = timezone.now()

        invoice_number = (
            f"INV-{now.strftime('%Y%m%d')}-"
            f"{uuid.uuid4().hex[:12].upper()}"
        )

        return BillingHistory.objects.create(
            employer=payment.employer,
            subscription=payment.subscription,
            transaction=payment,
            amount=payment.amount,
            currency=payment.currency,
            billing_period_start=now,
            billing_period_end=now,
            invoice_number=invoice_number,
            status=BillingHistory.PAID,
        )

    # ---------------------------------------------------------
    # INTERNAL SUCCESS HANDLER
    # ---------------------------------------------------------

    @staticmethod
    def _mark_payment_success(payment, message):
        """
        Marks a payment as successful and performs all
        financial bookkeeping.

        This includes:

        1. Payment status
        2. paid_at timestamp
        3. Billing history
        4. Suspicious transaction monitoring
        5. Financial audit log
        """

        payment.status = PaymentTransaction.SUCCESS
        payment.paid_at = timezone.now()

        payment.save(
            update_fields=[
                "status",
                "paid_at",
            ]
        )

        # Create billing history
        PaymentService._create_billing_history(
            payment
        )

        # Financial security monitoring
        FinancialSecurityService.log_suspicious_transaction(
            payment
        )

        # Financial audit log
        FinancialAuditLog.objects.create(
            transaction=payment,
            employer=payment.employer,
            action=FinancialAuditLog.PAYMENT_SUCCESS,
            message=message,
        )

        return payment

    # ---------------------------------------------------------
    # CREATE PAYMENT ORDER
    # ---------------------------------------------------------

    @transaction.atomic
    def create_order(
        self,
        employer,
        amount,
        currency="INR",
        subscription=None,
    ):
        """
        Creates a Razorpay order and stores a local
        PaymentTransaction record.
        """

        amount = Decimal(str(amount))

        if amount <= 0:
            raise ValueError(
                "Payment amount must be greater than zero."
            )

        amount_paise = int(amount * 100)

        receipt = (
            f"receipt_{uuid.uuid4().hex[:20]}"
        )

        order = self.client.order.create(
            data={
                "amount": amount_paise,
                "currency": currency,
                "receipt": receipt,
                "capture": "manual",
            }
        )

        payment_transaction = (
            PaymentTransaction.objects.create(
                employer=employer,
                subscription=subscription,
                amount=amount,
                currency=currency,
                transaction_id=order["id"],
                razorpay_order_id=order["id"],
                status=PaymentTransaction.PENDING,
            )
        )

        return {
            "transaction_id": (
                payment_transaction.transaction_id
            ),
            "razorpay_order_id": order["id"],
            "amount": amount,
            "amount_paise": amount_paise,
            "currency": currency,
            "status": payment_transaction.status,
            "key_id": settings.RAZORPAY_KEY_ID,
        }

    # ---------------------------------------------------------
    # VERIFY PAYMENT
    # ---------------------------------------------------------

    def verify_payment(
        self,
        employer,
        razorpay_order_id,
        razorpay_payment_id,
        razorpay_signature,
    ):
        """
        Verifies the Razorpay payment signature.

        Because the order is configured for manual capture,
        a valid signature does NOT mark the payment as SUCCESS.
        The payment becomes SUCCESS after capture.
        """

        payment = (
            PaymentTransaction.objects
            .filter(
                employer=employer,
                razorpay_order_id=razorpay_order_id,
            )
            .first()
        )

        if not payment:
            raise ValueError(
                "Payment transaction not found."
            )

        # Prevent duplicate processing
        if payment.razorpay_payment_id:

            if (
                payment.razorpay_payment_id
                == razorpay_payment_id
            ):
                return payment

            raise ValueError(
                "Payment has already been processed."
            )

        generated_signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            (
                f"{razorpay_order_id}|"
                f"{razorpay_payment_id}"
            ).encode(),
            hashlib.sha256,
        ).hexdigest()

        # Invalid signature
        if not hmac.compare_digest(
            generated_signature,
            razorpay_signature,
        ):

            payment.status = (
                PaymentTransaction.FAILED
            )

            payment.save(
                update_fields=[
                    "status",
                ]
            )

            FinancialAuditLog.objects.create(
                transaction=payment,
                employer=payment.employer,
                action=(
                    FinancialAuditLog.PAYMENT_FAILED
                ),
                message=(
                    "Payment verification failed "
                    "because the Razorpay signature "
                    "was invalid."
                ),
            )

            raise ValueError(
                "Invalid payment signature."
            )

        # Signature is valid.
        # Payment remains PENDING until capture.

        payment.razorpay_payment_id = (
            razorpay_payment_id
        )

        payment.razorpay_signature = (
            razorpay_signature
        )

        payment.save(
            update_fields=[
                "razorpay_payment_id",
                "razorpay_signature",
            ]
        )

        return payment

    # ---------------------------------------------------------
    # CAPTURE PAYMENT
    # ---------------------------------------------------------

    @transaction.atomic
    def capture_payment(
        self,
        employer,
        razorpay_payment_id,
        amount,
    ):
        """
        Captures a Razorpay payment.

        After successful capture:

        PaymentTransaction
                ↓
        SUCCESS
                ↓
        BillingHistory
                ↓
        FinancialAuditLog
                ↓
        Suspicious transaction check
        """

        payment = (
            PaymentTransaction.objects
            .filter(
                employer=employer,
                razorpay_payment_id=(
                    razorpay_payment_id
                ),
            )
            .first()
        )

        if not payment:
            raise ValueError(
                "Payment transaction not found."
            )

        amount_decimal = Decimal(str(amount))

        if amount_decimal <= 0:
            raise ValueError(
                "Payment amount must be greater than zero."
            )

        amount_paise = int(
            amount_decimal * 100
        )

        result = self.client.payment.capture(
            razorpay_payment_id,
            amount_paise,
            {
                "currency": payment.currency,
            },
        )

        self._mark_payment_success(
            payment,
            "Payment captured successfully.",
        )

        return result

    # ---------------------------------------------------------
    # WEBHOOK SIGNATURE VERIFICATION
    # ---------------------------------------------------------

    def verify_webhook_signature(
        self,
        payload,
        signature,
    ):
        """
        Verifies the Razorpay webhook signature.
        """

        expected_signature = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(
            expected_signature,
            signature,
        )

    # ---------------------------------------------------------
    # PROCESS WEBHOOK EVENTS
    # ---------------------------------------------------------

    @transaction.atomic
    def process_webhook_event(
        self,
        payload,
    ):
        """
        Processes Razorpay payment and refund webhook events.
        """

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

        # -----------------------------------------------------
        # PAYMENT EVENTS
        # -----------------------------------------------------

        if event in [
            "payment.captured",
            "payment.failed",
        ]:

            payment_id = payment_entity.get(
                "id"
            )

            payment = (
                PaymentTransaction.objects
                .filter(
                    razorpay_payment_id=payment_id
                )
                .first()
            )

            if not payment:
                return

            # PAYMENT CAPTURED
            if event == "payment.captured":

                # Avoid duplicate webhook processing
                if payment.status == (
                    PaymentTransaction.SUCCESS
                ):
                    return

                self._mark_payment_success(
                    payment,
                    (
                        "Payment captured successfully "
                        "through Razorpay webhook."
                    ),
                )

            # PAYMENT FAILED
            elif event == "payment.failed":

                payment.status = (
                    PaymentTransaction.FAILED
                )

                payment.save(
                    update_fields=[
                        "status",
                    ]
                )

                FinancialAuditLog.objects.create(
                    transaction=payment,
                    employer=payment.employer,
                    action=(
                        FinancialAuditLog.PAYMENT_FAILED
                    ),
                    message=(
                        "Payment failed according "
                        "to Razorpay webhook."
                    ),
                )

        # -----------------------------------------------------
        # REFUND EVENTS
        # -----------------------------------------------------

        elif event in [
            "refund.created",
            "refund.processed",
            "refund.failed",
        ]:

            payment_id = refund_entity.get(
                "payment_id"
            )

            payment = (
                PaymentTransaction.objects
                .filter(
                    razorpay_payment_id=payment_id
                )
                .first()
            )

            if not payment:
                return

            # REFUND PROCESSED
            if event == "refund.processed":

                payment.status = (
                    PaymentTransaction.REFUNDED
                )

                payment.save(
                    update_fields=[
                        "status",
                    ]
                )

            # REFUND FAILED
            elif event == "refund.failed":

                payment.status = (
                    PaymentTransaction.SUCCESS
                )

                payment.save(
                    update_fields=[
                        "status",
                    ]
                )

    # ---------------------------------------------------------
    # REFUND PAYMENT
    # ---------------------------------------------------------

    def refund_payment(
        self,
        transaction,
        amount=None,
        reason="",
    ):
        """
        Creates a Razorpay refund for a successful payment.
        """

        if transaction.status != (
            PaymentTransaction.SUCCESS
        ):
            raise ValueError(
                "Only successful payments can be refunded."
            )

        if not transaction.razorpay_payment_id:
            raise ValueError(
                "Razorpay payment ID is missing."
            )

        refund_data = {}

        if amount is not None:

            amount_decimal = Decimal(
                str(amount)
            )

            if amount_decimal <= 0:
                raise ValueError(
                    "Refund amount must be greater than zero."
                )

            amount_in_paise = int(
                amount_decimal * 100
            )

            refund_data["amount"] = (
                amount_in_paise
            )

        refund_data["notes"] = {
            "reason": reason[:256],
        }

        refund = self.client.payment.refund(
            transaction.razorpay_payment_id,
            refund_data,
        )

        return refund