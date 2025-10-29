# # main_app/models.py
from django.db import models
from django.contrib.auth.models import User

ROLE_CHOICES = [
    ('admin', 'Admin'),
    ('organizer', 'Organizer'),
    ('manager', 'Manager'),
    ('staff', 'Staff'),
]

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    is_available = models.BooleanField(default=True)
    current_team = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"
    

class Company(models.Model):
    name = models.CharField(max_length=200, unique=True)
    # created by either Admin or Organizer 
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_companies'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name