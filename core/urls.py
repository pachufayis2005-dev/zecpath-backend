from django.urls import path

from .views import (JobListAPIView,JobCreateAPIView,UserTestAPIView,)

urlpatterns = [
    path('jobs/', JobListAPIView.as_view()),
    path('jobs/create/', JobCreateAPIView.as_view()),
    path('users/test/', UserTestAPIView.as_view()),
]

