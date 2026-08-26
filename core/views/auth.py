from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from ..auth_serializers import SignupSerializer
from ..throttles import LoginRateThrottle


@extend_schema(
    summary="Login and get JWT tokens",
    description="Authenticate with username and password. Returns access and refresh tokens.",
    examples=[
        OpenApiExample(
            "Login request",
            value={"username": "john_doe", "password": "yourpassword123"},
            request_only=True,
        )
    ],
)
class LoginAPIView(TokenObtainPairView):
    """Authenticate a user and return JWT access + refresh tokens."""

    throttle_classes = [LoginRateThrottle]


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(
                {"error": "Invalid or missing refresh token"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class SignupAPIView(APIView):

    def post(self, request):

        serializer = SignupSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserTestAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "message": "Protected API Working",
                "user": request.user.username,
                "role": request.user.role,
            }
        )


class AuthTestAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        return Response(
            {
                "message": "Authentication working",
                "user": request.user.username,
                "user_id": request.user.id,
            }
        )