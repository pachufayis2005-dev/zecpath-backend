from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
from core.models import Application, Job



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

class JobPostingAPITest(APITestCase):

    def test_employer_can_post_job(self):
        signup_response = self.client.post("/api/signup/", {
            "username": "qa_employer1",
            "email": "qa_employer1@example.com",
            "phone": "9999999998",
            "role": "EMPLOYER",
            "password": "StrongPass123",
        })
        self.assertEqual(signup_response.status_code, status.HTTP_201_CREATED)

        login_response = self.client.post("/api/login/", {
            "username": "qa_employer1",
            "password": "StrongPass123",
        })
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        job_response = self.client.post("/api/jobs/create/", {
            "title": "Python Developer",
            "description": "Building backend systems with Django.",
            "skills": "Python, Django, PostgreSQL",
            "experience": "1-3 years",
            "salary": 600000,
            "location": "Remote",
            "job_type": "FULL_TIME",
            "status": "ACTIVE",
        })

        self.assertEqual(job_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(job_response.data["title"], "Python Developer")

    def test_candidate_cannot_post_job(self):
        signup_response = self.client.post("/api/signup/", {
            "username": "qa_candidate2",
            "email": "qa_candidate2@example.com",
            "phone": "9999999997",
            "role": "CANDIDATE",
            "password": "StrongPass123",
        })
        self.assertEqual(signup_response.status_code, status.HTTP_201_CREATED)

        login_response = self.client.post("/api/login/", {
            "username": "qa_candidate2",
            "password": "StrongPass123",
        })
        access_token = login_response.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        job_response = self.client.post("/api/jobs/create/", {
            "title": "Should Not Be Created",
            "description": "This should fail.",
            "skills": "N/A",
            "experience": "0",
            "salary": 100000,
            "location": "Remote",
            "job_type": "FULL_TIME",
            "status": "ACTIVE",
        })

        self.assertEqual(job_response.status_code, status.HTTP_403_FORBIDDEN)



class AIInterviewAPITest(APITestCase):

    def _create_employer_and_job(self):
        self.client.post("/api/signup/", {
            "username": "qa_employer2",
            "email": "qa_employer2@example.com",
            "phone": "9999999996",
            "role": "EMPLOYER",
            "password": "StrongPass123",
        })
        login = self.client.post("/api/login/", {
            "username": "qa_employer2",
            "password": "StrongPass123",
        })
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        job_response = self.client.post("/api/jobs/create/", {
            "title": "Django Developer",
            "description": "Backend role.",
            "skills": "Python, Django",
            "experience": "1-3 years",
            "salary": 700000,
            "location": "Remote",
            "job_type": "FULL_TIME",
            "status": "ACTIVE",
        })
        self.client.credentials()  # clear employer auth
        return job_response.data["id"]

    @patch("core.views.applications.send_email_task.delay")
    @patch("core.views.applications.process_interview_calls.delay")
    @patch("core.views.applications.check_candidate_eligibility", return_value=True)
    @patch("core.views.applications.calculate_ats_score", return_value={"score": 90})
    def test_candidate_apply_triggers_interview_session(
        self, mock_ats, mock_eligible, mock_process_calls, mock_email
    ):
        job_id = self._create_employer_and_job()

        self.client.post("/api/signup/", {
            "username": "qa_candidate3",
            "email": "qa_candidate3@example.com",
            "phone": "9999999995",
            "role": "CANDIDATE",
            "password": "StrongPass123",
        })
        login = self.client.post("/api/login/", {
            "username": "qa_candidate3",
            "password": "StrongPass123",
        })
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        apply_response = self.client.post(f"/api/jobs/{job_id}/apply/", {
            "cover_letter": "I am excited to apply for this role.",
        })

        self.assertEqual(apply_response.status_code, status.HTTP_201_CREATED)

        application = Application.objects.get(id=apply_response.data["id"])
        self.assertEqual(application.ats_score, 90)
        self.assertTrue(hasattr(application, "interview_call"))

        interview_call = application.interview_call
        session = interview_call.aiinterviewsession_set.first()
        self.assertIsNotNone(session)

        first_question = session.aiquestion_set.first()
        self.assertIsNotNone(first_question)

        answer_response = self.client.post(
            f"/api/ai-answer/{first_question.id}/submit/",
            {"answer": "I have three years of experience with Django and Python, building REST APIs."},
        )

        self.assertEqual(answer_response.status_code, status.HTTP_200_OK)
        self.assertIn("score", answer_response.data)