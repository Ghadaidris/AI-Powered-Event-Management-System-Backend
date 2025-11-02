# backend/main_app/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Company, Event


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
        fields = ['username', 'email', 'role', 'is_available', 'current_team']


class CompanySerializer(serializers.ModelSerializer):
    created_by = UserProfileSerializer(read_only=True)

    class Meta:
        model = Company
        fields = '__all__'


class EventSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    assigned_staff = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = '__all__'