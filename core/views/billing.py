import json

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import (
    BillingHistory,
    FinancialAuditLog,
    PaymentTransaction,
    RefundRecord,
)
from ..permissions import IsAdmin, IsEmployer
from ..serializers import (
    BillingHistorySerializer,
    PaymentTransactionSerializer,
    RefundRecordSerializer,
)
from ..services.billing_service import BillingService
from ..services.payment_service import PaymentService
from ..services.subscription_service import get_subscription_status


class CreatePaymentOrderAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    def post(self, request):

        employer = request.user.employer

        amount = request.data.get("amount")
        currency = request.data.get("currency", "INR")

        if not amount:
            return Response(
                {"error": "amount is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            data = PaymentService().create_order(
                employer=employer,
                amount=amount,
                currency=currency,
            )

            return Response(data, status=status.HTTP_201_CREATED)

        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception:
            return Response(
                {"error": "Unable to create payment order."},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class VerifyPaymentAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    def post(self, request):

        employer = request.user.employer

        razorpay_order_id = request.data.get("razorpay_order_id")
        razorpay_payment_id = request.data.get("razorpay_payment_id")
        razorpay_signature = request.data.get("razorpay_signature")

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return Response(
                {"error": "Payment verification fields are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment = PaymentService().verify_payment(
                employer=employer,
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_signature=razorpay_signature,
            )

            return Response(
                {
                    "message": "Payment verified successfully.",
                    "transaction_id": payment.transaction_id,
                    "payment_id": payment.razorpay_payment_id,
                    "status": payment.status,
                },
                status=status.HTTP_200_OK,
            )

        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class CapturePaymentAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    def post(self, request):

        employer = request.user.employer

        payment_id = request.data.get("razorpay_payment_id")
        amount = request.data.get("amount")

        if not payment_id or not amount:
            return Response(
                {"error": "razorpay_payment_id and amount are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = PaymentService().capture_payment(
                employer=employer,
                razorpay_payment_id=payment_id,
                amount=amount,
            )

            return Response(
                {
                    "message": "Payment captured successfully.",
                    "payment": result,
                },
                status=status.HTTP_200_OK,
            )

        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception:
            return Response(
                {"error": "Unable to capture payment."},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class RazorpayWebhookAPIView(APIView):

    permission_classes = [AllowAny]

    authentication_classes = []

    def post(self, request):

        signature = request.headers.get("X-Razorpay-Signature")

        if not signature:
            return Response(
                {"error": "Webhook signature missing."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_body = request.body

        if not PaymentService().verify_webhook_signature(raw_body, signature):
            return Response(
                {"error": "Invalid webhook signature."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            return Response(
                {"error": "Invalid webhook payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        PaymentService().process_webhook_event(payload)

        return Response(
            {"message": "Webhook received successfully."},
            status=status.HTTP_200_OK,
        )


class SubscriptionStatusAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    def get(self, request):

        employer = request.user.employer

        data = get_subscription_status(employer)

        return Response(data, status=status.HTTP_200_OK)


class AdminTransactionListAPIView(APIView):

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):

        transactions = PaymentTransaction.objects.select_related(
            "employer", "subscription__plan"
        ).order_by("-created_at")

        serializer = PaymentTransactionSerializer(transactions, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminBillingHistoryAPIView(APIView):

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):

        records = BillingHistory.objects.select_related(
            "employer", "subscription__plan", "transaction"
        ).order_by("-created_at")

        serializer = BillingHistorySerializer(records, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class DailyRevenueAPIView(APIView):

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):

        data = BillingService.daily_revenue()

        return Response(data, status=status.HTTP_200_OK)


class MonthlyRevenueAPIView(APIView):

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):

        data = BillingService.monthly_revenue()

        return Response(data, status=status.HTTP_200_OK)


class PlanWiseRevenueAPIView(APIView):

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):

        data = BillingService.plan_wise_revenue()

        return Response(data, status=status.HTTP_200_OK)


class RevenueSummaryAPIView(APIView):

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):

        total = BillingService.total_revenue()

        return Response(
            {
                "total_revenue": total,
                "currency": "INR",
            },
            status=status.HTTP_200_OK,
        )


class AdminRefundAPIView(APIView):

    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, pk):

        transaction_obj = get_object_or_404(PaymentTransaction, pk=pk)

        amount = request.data.get("amount")
        reason = request.data.get("reason", "Admin initiated refund")

        try:
            refund = PaymentService().refund_payment(
                transaction=transaction_obj,
                amount=amount,
                reason=reason,
            )

            refund_record = RefundRecord.objects.create(
                transaction=transaction_obj,
                employer=transaction_obj.employer,
                refund_id=refund["id"],
                amount=(refund["amount"] / 100),
                currency=refund.get("currency", transaction_obj.currency),
                reason=reason,
                status=RefundRecord.PROCESSED,
                processed_at=timezone.now(),
            )

            transaction_obj.status = PaymentTransaction.REFUNDED
            transaction_obj.save(update_fields=["status"])

            FinancialAuditLog.objects.create(
                transaction=transaction_obj,
                employer=transaction_obj.employer,
                action=FinancialAuditLog.REFUND_CREATED,
                message=(
                    f"Refund {refund_record.refund_id} "
                    f"created for transaction "
                    f"{transaction_obj.transaction_id}."
                ),
                ip_address=request.META.get("REMOTE_ADDR"),
            )

            return Response(
                RefundRecordSerializer(refund_record).data,
                status=status.HTTP_201_CREATED,
            )

        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as exc:

            FinancialAuditLog.objects.create(
                transaction=transaction_obj,
                employer=transaction_obj.employer,
                action=FinancialAuditLog.REFUND_FAILED,
                message=str(exc),
                ip_address=request.META.get("REMOTE_ADDR"),
            )

            return Response(
                {"error": "Refund failed."},
                status=status.HTTP_502_BAD_GATEWAY,
            )