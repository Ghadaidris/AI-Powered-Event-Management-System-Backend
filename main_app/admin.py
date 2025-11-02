from django.contrib import admin
from .models import UserProfile, Company
# # from django.contrib.auth.models import User
admin.site.register(UserProfile)
admin.site.register(Company)
