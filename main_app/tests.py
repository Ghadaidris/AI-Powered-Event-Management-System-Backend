from django.test import TestCase
from django.contrib.auth.models import User
from .models import (
    UserProfile, Company, Event, Team, Mission, Task
)
from datetime import date


class ModelsTest(TestCase):
    def setUp(self):
        # === Users & Profiles ===
        self.user_admin = User.objects.create_user(username='admin_user', password='123')
        self.user_manager = User.objects.create_user(username='manager_user', password='123')
        self.user_staff = User.objects.create_user(username='staff_user', password='123')

        self.profile_admin = UserProfile.objects.create(user=self.user_admin, role='admin')
        self.profile_manager = UserProfile.objects.create(user=self.user_manager, role='manager')
        self.profile_staff = UserProfile.objects.create(user=self.user_staff, role='staff')

        # === Company ===
        self.company = Company.objects.create(
            name='Eventify Co',
            created_by=self.profile_admin
        )

        # === Event ===
        self.event = Event.objects.create(
            title='AI Expo',
            location='Riyadh',
            description='Annual AI Exhibition',
            date=date(2025, 11, 10),
            company=self.company,
            created_by=self.profile_admin
        )

        # === Team ===
        self.team = Team.objects.create(
            name='Tech Setup Team',
            manager=self.profile_manager,
            event=self.event,
            created_by=self.profile_admin
        )
        self.team.members.add(self.profile_staff)

        # === Mission ===
        self.mission = Mission.objects.create(
            title='Prepare Stage Setup',
            description='Setup lighting and screens',
            event=self.event,
            team=self.team,
            created_by=self.profile_admin,
            assigned_manager=self.profile_manager,
            ai_split=False,
            is_approved=True,
            status='in_progress'
        )

        # === Task ===
        self.task = Task.objects.create(
            title='Install LED screens',
            description='Handle main stage screens',
            mission=self.mission,
            assignee=self.profile_staff,
            team=self.team,
            event=self.event,
            created_by=self.profile_manager,
            status='pending',
            ai_generated=True
        )

    # ===============================
    # 🔹 String Representations
    # ===============================
    def test_userprofile_str(self):
        self.assertEqual(str(self.profile_manager), 'manager_user - manager')

    def test_company_str(self):
        self.assertEqual(str(self.company), 'Eventify Co')

    def test_event_str(self):
        self.assertEqual(str(self.event), 'AI Expo')

    def test_team_str(self):
        self.assertEqual(str(self.team), 'Tech Setup Team (AI Expo)')

    def test_mission_str(self):
        self.assertEqual(str(self.mission), 'Mission: Prepare Stage Setup (Tech Setup Team - AI Expo)')

    def test_task_str(self):
        self.assertEqual(str(self.task), 'Install LED screens (sub of Prepare Stage Setup)')

    # ===============================
    # 🔹 Relationships
    # ===============================
    def test_team_event_relationship(self):
        self.assertEqual(self.team.event, self.event)
        self.assertIn(self.team, self.event.teams.all())

    def test_mission_relationships(self):
        self.assertEqual(self.mission.team, self.team)
        self.assertEqual(self.mission.event, self.event)
        self.assertEqual(self.mission.assigned_manager, self.profile_manager)

    def test_task_relationships(self):
        self.assertEqual(self.task.mission, self.mission)
        self.assertEqual(self.task.assignee, self.profile_staff)
        self.assertEqual(self.task.team, self.team)
        self.assertEqual(self.task.event, self.event)

    def test_team_membership(self):
        self.assertIn(self.profile_staff, self.team.members.all())

    # ===============================
    # 🔹 Cascade Deletions
    # ===============================
    def test_delete_company_cascades_to_events(self):
        self.company.delete()
        self.assertEqual(Event.objects.count(), 0)

    def test_delete_event_cascades_to_teams_missions_tasks(self):
        self.event.delete()
        self.assertEqual(Team.objects.count(), 0)
        self.assertEqual(Mission.objects.count(), 0)
        self.assertEqual(Task.objects.count(), 0)

    def test_delete_team_cascades_to_missions_and_tasks(self):
        self.team.delete()
        self.assertEqual(Mission.objects.count(), 0)
        self.assertEqual(Task.objects.count(), 0)

    def test_delete_user_cascades_to_profile(self):
        self.user_manager.delete()
        self.assertEqual(UserProfile.objects.filter(role='manager').count(), 0)

    # ===============================
    # 🔹 Logic Tests
    # ===============================
    def test_mission_approval_and_status(self):
        mission = self.mission
        self.assertTrue(mission.is_approved)
        self.assertEqual(mission.status, 'in_progress')

    def test_task_status_update(self):
        self.task.status = 'done'
        self.task.save()
        updated_task = Task.objects.get(id=self.task.id)
        self.assertEqual(updated_task.status, 'done')

    def test_ai_generated_task_flag(self):
        self.assertTrue(self.task.ai_generated)
