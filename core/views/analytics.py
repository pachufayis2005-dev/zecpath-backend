from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from ..permissions import IsEmployer
from ..services import AnalyticsService
from ..services.subscription_service import can_view_ai_analytics, can_view_analytics
from ..throttles import PremiumAPIRateThrottle


@method_decorator(cache_page(60), name="dispatch")
class HiringFunnelAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    throttle_classes = [PremiumAPIRateThrottle]

    def get(self, request):

        employer = request.user.employer

        if not can_view_analytics(employer):
            return Response(
                {"error": "Your subscription does not allow access to analytics."},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = AnalyticsService().hiring_funnel()

        return Response(data)


@method_decorator(cache_page(60), name="dispatch")
class JobPerformanceAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    throttle_classes = [PremiumAPIRateThrottle]

    def get(self, request):

        employer = request.user.employer

        if not can_view_analytics(employer):
            return Response(
                {"error": "Your subscription does not allow access to analytics."},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = AnalyticsService().job_performance()

        return Response(data)


@method_decorator(cache_page(60), name="dispatch")
class ConversionRatioAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    throttle_classes = [PremiumAPIRateThrottle]

    def get(self, request):

        employer = request.user.employer

        if not can_view_analytics(employer):
            return Response(
                {"error": "Your subscription does not allow access to analytics."},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = AnalyticsService().conversion_ratios()

        return Response(data)


class AIAnalyticsAPIView(APIView):

    permission_classes = [IsAuthenticated, IsEmployer]

    throttle_classes = [PremiumAPIRateThrottle]

    def get(self, request):

        employer = request.user.employer

        if not can_view_ai_analytics(employer):
            return Response(
                {"error": "Your subscription does not allow access to AI analytics."},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = AnalyticsService().ai_analytics(employer)

        return Response(data)