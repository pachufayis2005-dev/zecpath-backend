from core.models import AIAnswer


class CandidateReportService:
    """
    Builds the final AI candidate report.
    """

    def generate_report(self, application):
        candidate = application.candidate.user.username
        job = application.job.title

        answers = AIAnswer.objects.filter(
            question__session__interview_call__application=application
        )

        strengths = []

        if application.ats_score >= 70:
            strengths.append("Strong ATS score")

        if answers.exists():
            strengths.append("Completed AI interview")

        risks = []

        if application.ats_score < 60:
            risks.append("Low ATS score")

        if answers.count() < 5:
            risks.append("Few interview answers")

        total_score = 0

        for answer in answers:
            total_score += answer.final_score

        if answers.exists():
            ai_score = round(total_score / answers.count(), 2)
        else:
            ai_score = 0

        summary = (
            f"{candidate} applied for {job}. "
            f"ATS Score: {application.ats_score}. "
            f"AI Interview Score: {ai_score}."
        )

        report = {
            "candidate": candidate,
            "job": job,
            "ats_score": application.ats_score,
            "ai_interview_score": ai_score,
            "answer_count": answers.count(),
            "strengths": strengths,
            "risks": risks,
            "summary": summary,
        }

        return report