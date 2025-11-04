from rest_framework import generics, status, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
import json  # مهم لتحويل members من string إلى list

from .models import UserProfile, Company, Event, Team, Task, Mission
from .serializers import (
    UserSerializer,
    UserProfileSerializer,
    CompanySerializer,
    EventSerializer,
    TeamSerializer,
    TaskSerializer,
    MissionSerializer
)


# --- Auth ---
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


# --- Profiles ---
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


# --- Company ---
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


# --- Event ---
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


# --- Team ---
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


# --- Task ---
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


# --- AI Logic Placeholder ---
class TaskSplitAI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        profile = UserProfile.objects.get(user=request.user)
        task = Task.objects.get(pk=pk)

        if profile.role not in ['organizer', 'manager']:
            return Response({'error': 'Unauthorized'}, status=403)

        if profile.role == 'manager' and task.team.manager != profile:
            return Response({'error': 'Not your team’s task'}, status=403)

        members = task.team.members.all()
        subtasks = []
        for member in members:
            sub = Task.objects.create(
                title=f"Subtask for {member.user.username}",
                description=f"Part of {task.title}",
                assignee=member,
                event=task.event,
                team=task.team,
                parent_task=task
            )
            subtasks.append(TaskSerializer(sub).data)

        task.is_split = True
        task.save()

        return Response({
            'message': 'Task successfully split into subtasks.',
            'subtasks': subtasks
        })


class ManagerTeamList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'manager':
            return Response({"error": "Not allowed"}, status=403)
        teams = Team.objects.filter(manager=profile)
        serializer = TeamSerializer(teams, many=True)
        return Response(serializer.data)


class ManagerTaskList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'manager':
            return Response({"error": "Not allowed"}, status=403)
        tasks = Task.objects.filter(
            assignee=profile) | Task.objects.filter(team__manager=profile)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)


# --- Mission ---
class MissionListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = UserProfile.objects.get(user=request.user)
        if profile.role == 'organizer':
            missions = Mission.objects.all()
        elif profile.role == 'manager':
            missions = Mission.objects.filter(team__manager=profile)
        else:
            missions = Mission.objects.filter(team__members=profile)
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


# --- AI Mission Assignment ---
class MissionAssignAI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != "manager":
            return Response({"error": "Only managers can use AI assignment"}, status=403)

        try:
            mission = Mission.objects.get(pk=pk, team__manager=profile)
        except Mission.DoesNotExist:
            return Response({"error": "Mission not found or not your team’s mission"}, status=404)

        team_members = mission.team.members.all()
        if not team_members.exists():
            return Response({"error": "No members in the team"}, status=400)

        subtasks = []
        for i, member in enumerate(team_members, start=1):
            sub = Task.objects.create(
                title=f"Task {i} for {member.user.username}",
                description=f"Auto-generated from mission '{mission.title}'",
                assignee=member,
                event=mission.event,
                team=mission.team,
                parent_mission=mission
            )
            subtasks.append(TaskSerializer(sub).data)

        mission.is_distributed = True
        mission.save()

        return Response({
            "message": "AI distributed tasks successfully",
            "subtasks": subtasks
        }, status=201)


class ManagerApproveTasks(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != "manager":
            return Response({"error": "Only managers can approve tasks"}, status=403)

        try:
            mission = Mission.objects.get(pk=pk, team__manager=profile)
        except Mission.DoesNotExist:
            return Response({"error": "Mission not found or not your team’s mission"}, status=404)

        tasks = Task.objects.filter(parent_mission=mission)
        updates = request.data.get("updates", [])
        for update in updates:
            try:
                task = tasks.get(id=update["id"])
                serializer = TaskSerializer(task, data=update, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
            except Task.DoesNotExist:
                continue

        mission.is_approved = True
        mission.save()

        return Response({"message": "Tasks updated and approved successfully."}, status=200)


# --- Add Member to Team ---
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
