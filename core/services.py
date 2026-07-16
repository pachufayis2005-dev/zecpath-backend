from .models import Application


def auto_shortlist(application):

    score = application.ats_score

    if score >= 80:
        application.status = Application.SHORTLISTED

    elif score < 50:
        application.status = Application.REJECTED

    else:
        application.status = Application.APPLIED

    application.save()

    return application

def check_candidate_eligibility(job, parsed_resume):

    ats_result = calculate_ats_score(
        job,
        parsed_resume
    )

    if ats_result["score"] >= 50:

        return True

    return False

def process_pending_applications():

    pending = Application.objects.filter(
        status=Application.APPLIED
    )

    updated = 0

    for application in pending:

        auto_shortlist(application)

        updated += 1

    return updated