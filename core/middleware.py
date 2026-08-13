from django.http import JsonResponse

from core.services.subscription_service import get_active_subscription


class SubscriptionRequiredMiddleware:
    """
    Premium subscription middleware.

    Subscription authentication and authorization are handled
    by DRF permission classes and the subscription service.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)