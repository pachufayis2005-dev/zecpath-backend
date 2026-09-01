from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status

from core.models import Job

User = get_user_model()


class AuthenticationTest(TestCase):

    def test_create_user(self):

        user = User.objects.create_user(
            username="testuser", email="test@test.com", password="password123"
        )

        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@test.com")


class JobModelTest(TestCase):

    def test_job_title(self):

        job = Job(title="Python Developer")

        self.assertEqual(job.title, "Python Developer")


class SignupAPITest(APITestCase):

    def test_signup_creates_candidate_and_returns_201(self):
        response = self.client.post("/api/signup/", {
            "username": "qa_candidate1",
            "email": "qa_candidate1@example.com",
            "phone": "9999999999",
            "role": "CANDIDATE",
            "password": "StrongPass123",
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="qa_candidate1").exists())

    def test_signup_fails_with_duplicate_email(self):
        User.objects.create_user(
            username="existing_user",
            email="dupe@example.com",
            password="pass123",
            role="CANDIDATE",
        )

        response = self.client.post("/api/signup/", {
            "username": "another_user",
            "email": "dupe@example.com",
            "phone": "8888888888",
            "role": "CANDIDATE",
            "password": "StrongPass123",
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)