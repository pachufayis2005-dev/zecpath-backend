from django.http import JsonResponse

from core.services.subscription_service import get_active_subscription


class SubscriptionRequiredMiddleware:
    """
    Protect selected premium API paths.

    Only employer accounts are checked.
    """

    PROTECTED_PATHS = {
        "/api/analytics/ai/",
        "/api/analytics/funnel/",
        "/api/analytics/jobs/",
        "/api/analytics/conversion/",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.path in self.PROTECTED_PATHS:
            if not request.user.is_authenticated:
                return JsonResponse(
                    {"error": "Authentication required."},
                    status=401,
                )

            if not hasattr(request.user, "employer"):
                return JsonResponse(
                    {"error": "Employer account required."},
                    status=403,
                )

            subscription = get_active_subscription(
                request.user.employer
            )

            if not subscription:
                return JsonResponse(
                    {
                        "error": (
                            "Your subscription is inactive or expired."
                        )
                    },
                    status=403,
                )

        return self.get_response(request)