from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"


class PremiumAPIRateThrottle(UserRateThrottle):
    scope = "premium_api"
