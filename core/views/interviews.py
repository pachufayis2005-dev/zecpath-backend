from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import AIAnswer, Application, AvailabilitySlot, InterviewSchedule
from ..permissions import IsAdmin, IsEmployer
from ..serializers import AvailabilitySlotSerializer, SubmitAnswerSerializer
from ..services import AccessValidationService, AnswerEvaluator, AuditService
from ..services.report_service import CandidateReportService
from ..services.subscription_service import can_view_ai_analytics
from ..tasks import send_interview_reminders
from ..throttles import PremiumAPIRateThrottle


class SubmitAnswerAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, answer_id):

        ai_answer = get_object_or_404(
            AIAnswer.objects.select_related(
                "question__session__interview_call__application__candidate__user"
            ),
            id=answer_id,
        )

        candidate = ai_answer.question.session.interview_call.application.candidate

        if request.user != candidate.user:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = SubmitAnswerSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        ai_answer.answer = serializer.validated_data["answer"]
        ai_answer.save()

        evaluator = AnswerEvaluator()
        evaluator.evaluate(ai_answer)

        AuditService().log_action(
            user=request.user,
            action="Submitted AI interview answer",
            object_type="AIAnswer",
            object_id=ai_answer.id,
        )

        return Response(
            {
                "message": "Answer submitted successfully",
                "score": ai_answer.final_score,
                "feedback": ai_answer.ai_feedback,
            }
        )


class AnswerScoreAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        answer = get_object_or_404(
            AIAnswer.objects.select_related(
                "question__session__interview_call__application__candidate__user"
            ),
            pk=pk,
        )

        candidate = answer.question.session.interview_call.application.candidate

        if request.user != candidate.user:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "question": answer.question.question,
                "answer": answer.answer,
                "session_id": answer.question.session.id,
                "relevance_score": answer.relevance_score,
                "completeness_score": answer.completeness_score,
                "confidence_score": answer.confidence_score,
                "final_score": answer.final_score,
                "matched_keywords": answer.matched_keywords,
                "evaluated_at": answer.evaluated_at,
                "feedback": answer.ai_feedback,
            }
        )


class CreateAvailabilitySlotAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    def post(self, request):

        employer = request.user.employer

        data = request.data.copy()
        data["employer"] = employer.id

        serializer = AvailabilitySlotSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AvailabilityListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        slots = AvailabilitySlot.objects.filter(is_booked=False).order_by(
            "date", "start_time"
        )

        serializer = AvailabilitySlotSerializer(slots, many=True)

        return Response(serializer.data)


class BookInterviewAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        application_id = request.data.get("application_id")
        slot_id = request.data.get("slot_id")

        try:
            application = Application.objects.get(id=application_id)
            AccessValidationService.validate_application_owner(
                request.user, application
            )
            slot = AvailabilitySlot.objects.get(id=slot_id)
        except (Application.DoesNotExist, AvailabilitySlot.DoesNotExist):
            return Response(
                {"error": "Invalid application or slot"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if slot.is_booked:
            return Response(
                {"error": "Slot already booked"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        schedule = InterviewSchedule.objects.create(
            application=application,
            slot=slot,
            status=InterviewSchedule.SCHEDULED,
        )

        slot.is_booked = True
        slot.save()

        AuditService().log_action(
            user=request.user,
            action="Booked interview",
            object_type="InterviewSchedule",
            object_id=schedule.id,
        )

        return Response(
            {
                "message": "Interview booked successfully",
                "schedule_id": schedule.id,
            },
            status=status.HTTP_201_CREATED,
        )


class SendInterviewRemindersAPIView(APIView):

    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):

        send_interview_reminders.delay()

        return Response({"message": "Reminder task started"}, status=status.HTTP_200_OK)


class CandidateReportAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    throttle_classes = [PremiumAPIRateThrottle]

    def get(self, request, pk):

        employer = request.user.employer

        if not can_view_ai_analytics(employer):
            return Response(
                {
                    "error": "Your subscription does not allow access to candidate reports."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        application = get_object_or_404(Application, pk=pk)

        AccessValidationService.validate_application_job_owner(
            request.user, application
        )

        report = CandidateReportService().generate_report(application)

        return Response(report, status=status.HTTP_200_OK)