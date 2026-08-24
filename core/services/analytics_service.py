from django.db.models import Avg, Count, Q

from core.models import Application


class AnalyticsService:
    """
    Recruitment analytics service.
    """

    def hiring_funnel(self):

        return {
            "applied": Application.objects.filter(status=Application.APPLIED).count(),
            "under_review": Application.objects.filter(
                status=Application.UNDER_REVIEW
            ).count(),
            "shortlisted": Application.objects.filter(
                status=Application.SHORTLISTED
            ).count(),
            "interviewed": Application.objects.filter(
                status=Application.INTERVIEW_SCHEDULED
            ).count(),
            "selected": Application.objects.filter(status=Application.SELECTED).count(),
        }

    def job_performance(self):

        from core.models import Job

        jobs = Job.objects.annotate(
            applications=Count("application"),
            under_review=Count(
                "application",
                filter=Q(application__status=Application.UNDER_REVIEW),
            ),
            shortlisted=Count(
                "application",
                filter=Q(application__status=Application.SHORTLISTED),
            ),
            interviewed=Count(
                "application",
                filter=Q(application__status=Application.INTERVIEW_SCHEDULED),
            ),
            selected=Count(
                "application",
                filter=Q(application__status=Application.SELECTED),
            ),
            rejected=Count(
                "application",
                filter=Q(application__status=Application.REJECTED),
            ),
        )

        result = []

        for job in jobs:

            result.append(
                {
                    "job": job.title,
                    "applications": job.applications,
                    "under_review": job.under_review,
                    "shortlisted": job.shortlisted,
                    "interviewed": job.interviewed,
                    "selected": job.selected,
                    "rejected": job.rejected,
                }
            )

        return result

    def conversion_ratios(self):

        total = Application.objects.count()

        if total == 0:

            return {
                "total_applications": 0,
                "shortlist_rate": 0,
                "interview_rate": 0,
                "selection_rate": 0,
            }

        shortlisted = Application.objects.filter(status=Application.SHORTLISTED).count()

        interviewed = Application.objects.filter(
            status=Application.INTERVIEW_SCHEDULED
        ).count()

        selected = Application.objects.filter(status=Application.SELECTED).count()

        return {
            "total_applications": total,
            "shortlist_rate": round(
                shortlisted / total * 100,
                2,
            ),
            "interview_rate": round(
                interviewed / total * 100,
                2,
            ),
            "selection_rate": round(
                selected / total * 100,
                2,
            ),
        }

    def ai_analytics(self, employer):

        from core.models import AIAnswer

        answers = AIAnswer.objects.filter(
            question__session__interview_call__application__job__employer=employer
        )

        total_answers = answers.count()

        if total_answers == 0:

            return {
                "total_answers": 0,
                "average_score": 0,
                "average_relevance": 0,
                "average_completeness": 0,
                "average_confidence": 0,
            }

        averages = answers.aggregate(
            average_score=Avg("final_score"),
            average_relevance=Avg("relevance_score"),
            average_completeness=Avg("completeness_score"),
            average_confidence=Avg("confidence_score"),
        )

        return {
            "total_answers": total_answers,
            "average_score": round(
                averages["average_score"] or 0,
                2,
            ),
            "average_relevance": round(
                averages["average_relevance"] or 0,
                2,
            ),
            "average_completeness": round(
                averages["average_completeness"] or 0,
                2,
            ),
            "average_confidence": round(
                averages["average_confidence"] or 0,
                2,
            ),
        }
