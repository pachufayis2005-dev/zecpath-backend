from django.urls import path
from .views import (
    SignupAPIView,
    LoginAPIView,
    JobListAPIView,
    JobCreateAPIView,
    UserTestAPIView,
    AdminAPIView,
    CandidateProfileAPIView,
    EmployerProfileAPIView,
)

urlpatterns = [
    path('signup/', SignupAPIView.as_view()),
    path('login/', LoginAPIView.as_view()),
    path('jobs/', JobListAPIView.as_view()),
    path('jobs/create/', JobCreateAPIView.as_view()),
    path('users/test/', UserTestAPIView.as_view()),
    path('admin/test/', AdminAPIView.as_view()),
    path('candidate/profile/',CandidateProfileAPIView.as_view()),
    path('employer/profile/',EmployerProfileAPIView.as_view()),
]