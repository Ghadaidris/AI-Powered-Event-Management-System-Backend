from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Company, Event, Team, Task, Mission 


# ===============================
# 🔹 User & Profile
# ===============================
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'role', 'is_available', 'current_team']


# ===============================
# 🔹 Company
# ===============================
class CompanySerializer(serializers.ModelSerializer):
    created_by = UserProfileSerializer(read_only=True)

    class Meta:
        model = Company
        fields = '__all__'


# ===============================
# 🔹 Event
# ===============================
class EventSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.user.username', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'location', 'description', 'date',
            'created_by', 'created_by_name', 'company', 'company_name'
        ]
        extra_kwargs = {
            'created_by': {'read_only': True},
            'company': {'required': False, 'allow_null': True}
        }


# ===============================
# 🔹 Team
# ===============================
# serializers.py


class TeamSerializer(serializers.ModelSerializer):
    manager_name = serializers.CharField(source='manager.user.username', read_only=True)
    member_names = serializers.SerializerMethodField()  # NEW
    created_by_name = serializers.CharField(source='created_by.user.username', read_only=True)

    class Meta:
        model = Team
        fields = [
            'id', 'name', 'manager', 'manager_name',
            'members', 'member_names', 'event',  # member_names included
            'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['created_by', 'created_at']

    def get_member_names(self, obj):
        return [member.user.username for member in obj.members.all()]

    # Handle ManyToMany in create
    def create(self, validated_data):
        members_data = validated_data.pop('members', [])
        team = Team.objects.create(**validated_data)
        if members_data:
            team.members.set(members_data)
        return team


# ===============================
# 🔹 Task
# ===============================
class TaskSerializer(serializers.ModelSerializer):
    assignee_name = serializers.CharField(source='assignee.user.username', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)
    mission_title = serializers.CharField(source='mission.title', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description',
            'mission', 'mission_title',
            'assignee', 'assignee_name',
            'team', 'team_name',
            'event', 'event_title',
            'created_by', 'created_at',
            'status', 'approved', 'ai_generated'
        ]
        read_only_fields = ['created_by', 'created_at']


# ===============================
# 🔹 Mission
# ===============================
class MissionSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.user.username', read_only=True)
    assigned_manager_name = serializers.CharField(source='assigned_manager.user.username', read_only=True)
    subtasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Mission
        fields = [
            'id', 'title', 'description', 'event', 'team', 'created_by',
            'assigned_manager', 'assigned_manager_name', 
            'ai_split', 'is_approved', 'event_title', 'team_name', 
            'created_by_name', 'subtasks'
        ]
