from django.contrib import admin
from .models import UserProfile, Company
# # from django.contrib.auth.models import User

# # @admin.register(Company)
# # class CompanyAdmin(admin.ModelAdmin):
# #     list_display = ('name', 'created_by', 'created_at')
# #     search_fields = ('name',)
# #     list_filter = ('created_at',)

admin.site.register(UserProfile)
admin.site.register(Company)