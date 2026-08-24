from django.contrib import admin

from .models import (
    Application,
    AuditTrail,
    Candidate,
    Employer,
    Job,
    User,
)

admin.site.register(User)
admin.site.register(Employer)
admin.site.register(Candidate)
admin.site.register(Job)
admin.site.register(Application)
admin.site.register(AuditTrail)
