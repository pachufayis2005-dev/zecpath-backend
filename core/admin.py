# Register your models here.

from django.contrib import admin
from .models import User, Job, Application

admin.site.register(User)
admin.site.register(Job)
admin.site.register(Application)