from django.db import models
from django.contrib.auth.models import User

# ===============================
# 🔹 Global Choices
# ===============================
ROLE_CHOICES = [
    ('admin', 'Admin'),
    ('organizer', 'Organizer'),
    ('manager', 'Manager'),
    ('staff', 'Staff'),
]

TASK_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('in_progress', 'In Progress'),
    ('done', 'Done'),
    ('blocked', 'Blocked'),
]


# ===============================
# 🔹 User Profile
# ===============================
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    is_available = models.BooleanField(default=True)
    current_team = models.CharField(max_length=100, blank=True, null=True)
    username = models.CharField(max_length=150, default="default_user")

    def __str__(self):
        return f"{self.user.username} - {self.role}"


# ===============================
# 🔹 Company (created by admin)
# ===============================
class Company(models.Model):
    name = models.CharField(max_length=200, unique=True)
    created_by = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE, 
        null=True,
        related_name='created_companies'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ===============================
# 🔹 Event (belongs to a company)
# ===============================
class Event(models.Model):
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=200, default="Riyadh")
    description = models.TextField(blank=True, null=True)
    date = models.DateField()

    created_by = models.ForeignKey(
        UserProfile,
       on_delete=models.CASCADE,   # keep info even if creator deleted
        null=True,
        blank=True
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,  #  delete all events if company deleted
        null=True,
        blank=True
    )

    def __str__(self):
        return self.title


# ===============================
# 🔹 Team (belongs to an event)
# ===============================
class Team(models.Model):
    name = models.CharField(max_length=100)
    manager = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,   # manager can be null if deleted
        null=True,
        related_name="managed_teams"
    )
    members = models.ManyToManyField(
        UserProfile,
        related_name="teams",
        blank=True
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,  #  delete teams when event deleted
        related_name="teams"
    )
    created_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_teams"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        event_title = self.event.title if self.event else "No Event"
        return f"{self.name} ({event_title})"


# ===============================
# 🔹 Mission (created by organizer)
# ===============================
class Mission(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="missions"
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="missions"
    )

    created_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_missions"
    )

    assigned_manager = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_missions"
    )

    created_at = models.DateTimeField(auto_now_add=True)

   
    ai_split = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Mission: {self.title} ({self.team.name} - {self.event.title})"


# ===============================
# 🔹 Task (created by manager or AI)
# ===============================
class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    mission = models.ForeignKey(
        Mission,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subtasks" 
    )

    assignee = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tasks"
    )

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tasks"
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="tasks"
    )

    created_by = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="created_tasks"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='pending')
    ai_generated = models.BooleanField(default=False)

    def __str__(self):
        base = f"{self.title}"
        if self.mission:
            base += f" (sub of {self.mission.title})"
        return base