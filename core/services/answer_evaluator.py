from core.models import AIAnswer
from core.services.scoring_engine import ScoringEngine
from django.utils import timezone
from core.services.logging_service import LoggingService

class AnswerEvaluator:
    """
    Evaluates and stores interview answer scores.
    """

    def __init__(self):
        self.engine = ScoringEngine()

    def evaluate(self, ai_answer):

        answer = ai_answer.answer

        job_title = (
            ai_answer.question
            .session
            .interview_call
            .application
            .job
            .title
        )

        relevance, matched = self.engine.keyword_score(
            answer,
            job_title,
        )

        completeness = self.engine.completeness_score(
            answer,
        )

        confidence = self.engine.confidence_score(
            answer,
        )

        final = self.engine.final_score(
            relevance,
            completeness,
            confidence,
        )

        ai_answer.relevance_score = relevance
        ai_answer.completeness_score = completeness
        ai_answer.confidence_score = confidence
        ai_answer.final_score = final
        ai_answer.matched_keywords = matched

        ai_answer.ai_feedback = (
            f"Matched {len(matched)} keyword(s). "
            f"Overall score: {final}"
        )

        ai_answer.evaluated_at = timezone.now()

        ai_answer.save()

        LoggingService().log_ai_event(interview=ai_answer.question.session.interview_call,
        event=f"AI evaluated answer. Score: {final}",)

        return ai_answer