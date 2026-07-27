from core.models import AIQuestion


class QuestionEngine:
    """
    Generates interview questions dynamically
    based on the job role.
    """

    DEFAULT_QUESTIONS = [
        {
            "category": AIQuestion.INTRODUCTION,
            "question": "Tell me about yourself."
        },
        {
            "category": AIQuestion.EXPERIENCE,
            "question": "Describe your previous work experience."
        },
        {
            "category": AIQuestion.SKILLS,
            "question": "What are your strongest technical skills?"
        },
        {
            "category": AIQuestion.AVAILABILITY,
            "question": "When can you join our company?"
        },
        {
            "category": AIQuestion.SALARY,
            "question": "What are your salary expectations?"
        },
    ]

    DJANGO_QUESTIONS = [
        {
            "category": AIQuestion.SKILLS,
            "question": "Explain Django ORM."
        },
        {
            "category": AIQuestion.SKILLS,
            "question": "What is Django REST Framework?"
        },
    ]

    PYTHON_QUESTIONS = [
        {
            "category": AIQuestion.SKILLS,
            "question": "Explain Python decorators."
        },
        {
            "category": AIQuestion.SKILLS,
            "question": "Difference between list and tuple?"
        },
    ]

    def generate_questions(self, job_title):

        questions = list(self.DEFAULT_QUESTIONS)

        title = job_title.lower()

        if "django" in title:
            questions.extend(self.DJANGO_QUESTIONS)

        elif "python" in title:
            questions.extend(self.PYTHON_QUESTIONS)

        return questions