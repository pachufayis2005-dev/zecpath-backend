from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class AuthenticationTest(TestCase):

    def test_create_user(self):

        user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="password123"
        )

        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@test.com")

from core.models import Job


class JobModelTest(TestCase):

    def test_job_title(self):

        job = Job(
            title="Python Developer"
        )

        self.assertEqual(
            job.title,
            "Python Developer"
        )