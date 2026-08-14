from rest_framework import serializers
from .models import (Job, Application,SavedJob,AuditLog,AvailabilitySlot,InterviewSchedule,)
from .models import (
    Job,
    Application,
    SavedJob,
    AuditLog,
    AvailabilitySlot,
    InterviewSchedule,
    PaymentTransaction,
    BillingHistory,
    RefundRecord,
    FinancialAuditLog,
)


class JobSerializer(serializers.ModelSerializer):

    class Meta:
        model = Job

        fields = [
            "id",
            "title",
            "description",
            "skills",
            "experience",
            "salary",
            "location",
            "job_type",
            "status",
            "created_at",
            "updated_at",
            "is_featured",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class ApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Application

        fields = [
            "id",
            "job",
            "resume_snapshot",
            "status",
            "ats_score",
            "applied_at",
        ]

class SavedJobSerializer(serializers.ModelSerializer):

    class Meta:
        model = SavedJob

        fields = [
            "id",
            "job",
            "saved_at",
        ]

class AuditLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = AuditLog

        fields = [
            "id",
            "admin",
            "action",
            "created_at",
        ]

class SubmitAnswerSerializer(serializers.Serializer):
    answer = serializers.CharField()

class AvailabilitySlotSerializer(serializers.ModelSerializer):

    class Meta:

        model = AvailabilitySlot

        fields = "__all__"


class InterviewScheduleSerializer(serializers.ModelSerializer):

    class Meta:

        model = InterviewSchedule

        fields = "__all__"

class PaymentTransactionSerializer(serializers.ModelSerializer):

    employer_name = serializers.CharField(
        source="employer.company_name",
        read_only=True,
    )

    plan_name = serializers.CharField(
        source="subscription.plan.name",
        read_only=True,
    )

    class Meta:
        model = PaymentTransaction
        fields = [
            "id",
            "employer",
            "employer_name",
            "subscription",
            "plan_name",
            "amount",
            "currency",
            "transaction_id",
            "razorpay_order_id",
            "razorpay_payment_id",
            "payment_method",
            "status",
            "paid_at",
            "created_at",
        ]


class BillingHistorySerializer(serializers.ModelSerializer):

    employer_name = serializers.CharField(
        source="employer.company_name",
        read_only=True,
    )

    class Meta:
        model = BillingHistory
        fields = [
            "id",
            "employer",
            "employer_name",
            "subscription",
            "transaction",
            "amount",
            "currency",
            "billing_period_start",
            "billing_period_end",
            "invoice_number",
            "status",
            "created_at",
        ]


class RefundRecordSerializer(serializers.ModelSerializer):

    class Meta:
        model = RefundRecord
        fields = [
            "id",
            "transaction",
            "employer",
            "refund_id",
            "amount",
            "currency",
            "reason",
            "status",
            "created_at",
            "processed_at",
        ]


class FinancialAuditLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = FinancialAuditLog
        fields = "__all__"