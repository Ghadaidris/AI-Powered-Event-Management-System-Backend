from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import UserProfile, Company, Event, Team, Task, Mission
from .serializers import (
    UserSerializer, UserProfileSerializer, CompanySerializer,   
    EventSerializer, TeamSerializer, TaskSerializer, MissionSerializer
)

from .ai_service import suggest_mission, split_mission  # Gemini AI
import json
import re
from google import genai
client = genai.Client()



# ===============================
# Auth
# ===============================
class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        UserProfile.objects.update_or_create(
            user=user,
            defaults={'role': 'staff', 'is_available': True}
        )
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data,
            'role': 'staff'
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        if not username or not password:
            return Response({"error": "Username and password required"}, status=400)
        user = authenticate(username=username, password=password)
        if not user:
            return Response({"error": "Invalid Credentials"}, status=401)
        profile = UserProfile.objects.get(user=user)
        tokens = RefreshToken.for_user(user)
        return Response({
            "access": str(tokens.access_token),
            "refresh": str(tokens),
            "user": UserSerializer(user).data,
            "role": profile.role
        })


class VerifyUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = UserProfile.objects.get(user=request.user)
        refresh = RefreshToken.for_user(request.user)
        return Response({
            'refresh': str(refresh),
            'accessToken': str(refresh.access_token),
            'user': UserSerializer(request.user).data,
            'role': profile.role
        })


# ===============================
# Profiles
# ===============================
class ProfileList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profiles = UserProfile.objects.all()
        serializer = UserProfileSerializer(profiles, many=True)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_me(request):
    profile = UserProfile.objects.get(user=request.user)
    return Response({
        'id': profile.id,
        'username': request.user.username,
        'email': request.user.email,
        'role': profile.role
    })


class ProfileDetail(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        profile = UserProfile.objects.get(id=pk)
        current_user_profile = UserProfile.objects.get(user=request.user)
        if current_user_profile.role != 'admin':
            return Response({"error": "Admin only"}, status=403)
        role = request.data.get('role')
        if role not in ['staff', 'organizer', 'manager', 'admin']:
            return Response({"error": "Invalid role"}, status=400)
        profile.role = role
        profile.save()
        return Response(UserProfileSerializer(profile).data)


# ===============================
# Company
# ===============================
class CompanyListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        companies = Company.objects.all()
        return Response(CompanySerializer(companies, many=True).data)

    def post(self, request):
        serializer = CompanySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = UserProfile.objects.get(user=request.user)
        company = serializer.save(created_by=profile)
        return Response(CompanySerializer(company).data, status=201)


class CompanyDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        company = get_object_or_404(Company, pk=pk)
        return Response(CompanySerializer(company).data)

    def patch(self, request, pk):
        company = get_object_or_404(Company, pk=pk)
        serializer = CompanySerializer(
            company, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        company = get_object_or_404(Company, pk=pk)
        if company.event_set.exists():
            return Response(
                {"error": "Cannot delete a company that has related events."},
                status=status.HTTP_400_BAD_REQUEST
            )
        company.delete()
        return Response({"message": "Company deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


# ===============================
# Event
# ===============================
class EventListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = Event.objects.all()
        return Response(EventSerializer(events, many=True).data)

    def post(self, request):
        data = request.data.copy()
        profile = UserProfile.objects.get(user=request.user)
        data['created_by'] = profile.id
        if 'company' not in data or data['company'] in ['', None]:
            data['company'] = None
        serializer = EventSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        event = serializer.save()
        return Response(EventSerializer(event).data, status=201)


class EventDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        event = Event.objects.get(pk=pk)
        return Response(EventSerializer(event).data)

    def patch(self, request, pk):
        event = Event.objects.get(pk=pk)
        serializer = EventSerializer(event, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        event = Event.objects.get(pk=pk)
        event.delete()
        return Response(status=204)


# ===============================
# Team
# ===============================
class TeamListCreate(generics.ListCreateAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'organizer':
            return Response({'error': 'Only organizers can create teams'}, status=403)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class TeamDetail(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        profile = UserProfile.objects.get(user=request.user)
        team = Team.objects.get(pk=pk)
        if profile != team.created_by and profile.role != 'admin':
            return Response({'error': 'Only organizer or admin can edit this team'}, status=403)
        serializer = TeamSerializer(team, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(TeamSerializer(team).data)

    def delete(self, request, pk):
        profile = UserProfile.objects.get(user=request.user)
        team = Team.objects.get(pk=pk)
        if profile != team.created_by and profile.role != 'admin':
            return Response({'error': 'Only organizer or admin can delete this team'}, status=403)
        team.delete()
        return Response(status=204)


# ===============================
# Task
# ===============================
class TaskListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = UserProfile.objects.get(user=request.user)
        if profile.role == 'manager':
            tasks = Task.objects.filter(
                assignee=profile) | Task.objects.filter(team__manager=profile)
        elif profile.role == 'organizer':
            tasks = Task.objects.all()
        else:
            tasks = Task.objects.filter(assignee=profile)
        return Response(TaskSerializer(tasks, many=True).data)

    def post(self, request):
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'organizer':
            return Response({'error': 'Only organizers can create tasks'}, status=403)
        data = request.data.copy()
        serializer = TaskSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        return Response(TaskSerializer(task).data, status=201)


class TaskDetail(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        profile = UserProfile.objects.get(user=request.user)
        task = Task.objects.get(pk=pk)
        if profile.role == 'manager' and task.assignee != profile and task.team.manager != profile:
            return Response({'error': 'You cannot edit this task'}, status=403)
        serializer = TaskSerializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        return Response(TaskSerializer(task).data)

    def delete(self, request, pk):
        profile = UserProfile.objects.get(user=request.user)
        task = Task.objects.get(pk=pk)
        if profile.role not in ['organizer', 'admin'] and (profile != task.assignee and profile != task.team.manager):
            return Response({'error': 'You cannot delete this task'}, status=403)
        task.delete()
        return Response(status=204)


# ===============================
# Mission
# ===============================
class MissionListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = UserProfile.objects.get(user=request.user)
        if profile.role == 'organizer':
            missions = Mission.objects.all()
        elif profile.role == 'manager':
            missions = Mission.objects.filter(team__manager=profile)
        elif profile.role == 'staff':
            missions = Mission.objects.filter(team__members=profile)
        else:
            missions = Mission.objects.none()  # admin يشوف كله من Organizer
        return Response(MissionSerializer(missions, many=True).data)

    def post(self, request):
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'organizer':
            return Response({'error': 'Only organizers can create missions'}, status=403)
        data = request.data.copy()
        data['created_by'] = profile.id
        serializer = MissionSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        mission = serializer.save(created_by=profile)
        return Response(MissionSerializer(mission).data, status=201)
    
class MissionDetail(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        mission = Mission.objects.get(pk=pk)
        serializer = MissionSerializer(
            mission, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        profile = UserProfile.objects.get(user=request.user)
        mission = Mission.objects.get(pk=pk)
        if profile.role not in ['organizer', 'admin']:
            return Response({'error': 'Only organizers or admins can delete missions'}, status=403)
        mission.delete()
        return Response(status=204)


# ===============================
# Add Member to Team
# ===============================
class AddTeamMember(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        profile = UserProfile.objects.get(user=request.user)
        team = Team.objects.get(pk=pk)
        if profile.role not in ['organizer', 'admin']:
            return Response({'error': 'Not authorized'}, status=403)
        member_id = request.data.get('member_id')
        if not member_id:
            return Response({'error': 'member_id is required'}, status=400)
        try:
            member_profile = UserProfile.objects.get(id=member_id)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
        team.members.add(member_profile)
        team.save()
        return Response({'message': f'{member_profile.user.username} added to {team.name}'})

# ===============================
# Gemini AI: Organizer Suggest Mission 
# ===============================
class AISuggestMission(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        event_id = request.data.get('event')
        if not event_id:
            return Response({'error': 'Event ID required'}, status=400)

        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=404)

        # جمع كل أعضاء الفرق المرتبطة بالحدث
        team_members_usernames = []
        event_teams = event.teams.all()
        for team in event_teams:
            team_members_usernames.extend([member.user.username for member in team.members.all()])
        team_members_str = ', '.join(team_members_usernames) if team_members_usernames else 'No members'

        # تحسين البرومت ليكون أكثر تحديداً
        prompt = f"""
        You are a professional AI event planner. Your task is to create ONE realistic and actionable mission
        for this event, suitable to be assigned to the team manager. Consider the event details:

        - Event Title: {event.title}
        - Event Date: {event.date}
        - Event Location: {event.location}
        - Event Type: {event.event_type if hasattr(event, 'event_type') else 'General'}
        - Expected Attendees: {event.expected_attendees if hasattr(event, 'expected_attendees') else 'Unknown'}
        - Available Team Members: {team_members_str}

        Requirements:
        - Must be actionable and assignable to a manager.
        - Include a clear title (short, descriptive).
        - Include a description (1-2 sentences) explaining what needs to be done and why.
        - Consider potential challenges.

        Return ONLY a JSON in this exact format:
        {{
          "title": "short descriptive title",
          "description": "1-2 sentence explanation of the mission"
        }}
        """

        try:
            response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            text = response.text.strip()

            start = text.find('{')
            end = text.rfind('}') + 1
            if start == -1 or end == 0:
                return Response({'error': 'No JSON found in AI response'}, status=500)

            json_str = text[start:end]
            suggestion = json.loads(json_str)

            # اختيار أول فريق مرتبط بالحدث كـ default
            team = event_teams.first()
            if not team:
                return Response({'error': 'No team found for this event'}, status=400)

            manager = event.teams.first().manager 
            if not manager:
                return Response({'error': 'No manager assigned to the team'}, status=400)

            mission = Mission.objects.create(
                title=suggestion['title'],
                description=suggestion['description'],
                event=event,
                team=team,
                assigned_manager=manager,
                created_by=UserProfile.objects.get(user=request.user)
            )

            return Response({
                "mission": {
                    "id": mission.id,
                    "title": mission.title,
                    "description": mission.description,
                    "manager": manager.user.username
                }
            }, status=201)

        except json.JSONDecodeError as e:
            return Response({'error': f'Invalid JSON from AI: {str(e)}'}, status=500)
        except Exception as e:
            return Response({'error': f'Gemini failed: {str(e)}'}, status=500)

# ===============================
# AI Service: Dynamic Split Mission
# ===============================
def split_mission(title, description, team_members):
    """
    Dynamically split a mission into subtasks and assign each to a team member.
    team_members: QuerySet of UserProfile objects
    """
    subtasks = []
    staff_members = [member for member in team_members if member.role == 'staff']
    if not staff_members:
        return subtasks

    # Create 1 subtask per staff member
    for i, member in enumerate(staff_members, start=1):
        task_title = f"{title} - Subtask {i}"
        task_description = f"Task for {member.user.username}: {description[:50]}..."  # Short preview
        subtasks.append({
            "title": task_title,
            "description": task_description,
            "assignee": member.user.username
        })

    return subtasks


# ===============================
# AI Split Mission View (Dynamic)
# ===============================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_split_mission_view(request, mission_id):
    profile = UserProfile.objects.get(user=request.user)

    try:
        mission = Mission.objects.get(id=mission_id, assigned_manager=profile)
    except Mission.DoesNotExist:
        return Response({"error": "Mission not found or not assigned to you"}, status=404)

    team_members = mission.team.members.all()
    if not team_members.exists():
        return Response({"error": "No members in team"}, status=400)

    # Generate dynamic subtasks
    subtasks_data = split_mission(mission.title, mission.description or "", team_members)
    created_tasks = []

    for sub in subtasks_data:
        try:
            assignee = UserProfile.objects.get(user__username=sub['assignee'])
            task = Task.objects.create(
                title=sub['title'],
                description=sub.get('description', ''),
                mission=mission,
                assignee=assignee,
                team=mission.team,
                event=mission.event,
                ai_generated=True,
                created_by=profile
            )
            created_tasks.append(TaskSerializer(task).data)
        except UserProfile.DoesNotExist:
            continue  # Skip if user not found

    mission.ai_split = True
    mission.save()

    return Response({
        "subtasks": created_tasks,
        "message": "AI split successful"
    })

# ===============================
# Manager Approve & Edit AI Split Tasks
# ===============================
class ManagerApproveTasks(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        """
        Manager can edit AI-generated tasks and approve them for staff.
        Request data format:
        {
            "updates": [
                {"id": 12, "title": "New Title", "description": "Updated description", "assignee": "username"}
            ]
        }
        """
        manager_profile = UserProfile.objects.get(user=request.user)
        if manager_profile.role != "manager":
            return Response({"error": "Only managers can approve tasks"}, status=403)

        try:
            mission = Mission.objects.get(pk=pk, assigned_manager=manager_profile)
        except Mission.DoesNotExist:
            return Response({"error": "Mission not found or not assigned to you"}, status=404)

        tasks = Task.objects.filter(mission=mission, ai_generated=True)
        updates = request.data.get("updates", [])

        for update in updates:
            try:
                task = tasks.get(id=update["id"])
                # Update fields
                if "title" in update:
                    task.title = update["title"]
                if "description" in update:
                    task.description = update["description"]
                if "assignee" in update:
                    assignee = UserProfile.objects.filter(user__username=update["assignee"]).first()
                    if assignee:
                        task.assignee = assignee
                task.save()
            except Task.DoesNotExist:
                continue

        mission.is_approved = True  # بعد الموافقة يروح للـ staff رسمي
        mission.save()

        return Response({
            "message": "Tasks updated and approved successfully.",
            "subtasks": TaskSerializer(tasks, many=True).data
        }, status=200)



# ===============================
# DELETE handlers using get_object_or_404
# ===============================
@api_view(['DELETE'])
def delete_team(request, pk):
    team = get_object_or_404(Team, pk=pk)
    profile = UserProfile.objects.get(user=request.user)
    if profile != team.created_by and profile.role != 'admin':
        return Response({'error': 'Only organizer or admin can delete this team'}, status=403)
    team.delete()
    return Response({'message': 'Team deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['DELETE'])
def delete_mission(request, pk):
    mission = get_object_or_404(Mission, pk=pk)
    profile = UserProfile.objects.get(user=request.user)
    if profile.role not in ['organizer', 'admin']:
        return Response({'error': 'Only organizers or admins can delete missions'}, status=403)
    mission.delete()
    return Response({'message': 'Mission deleted successfully'}, status=status.HTTP_204_NO_CONTENT)



class StaffUpdateTaskStatus(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        profile = UserProfile.objects.get(user=request.user)
        
        # السماح فقط للstaff اللي مخصص له المهمة
        try:
            task = Task.objects.get(pk=pk, assignee=profile)
        except Task.DoesNotExist:
            return Response({'error': 'Task not found or not assigned to you'}, status=404)

        status_value = request.data.get('status')
        if not status_value:
            return Response({'error': 'status field is required'}, status=400)
        
        task.status = status_value
        task.save()
        return Response(TaskSerializer(task).data, status=200)