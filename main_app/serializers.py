
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Company, Event

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)  
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']  
        )
      
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer() 
    class Meta:
        model = UserProfile
        fields = '__all__'

class CompanySerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    class Meta:
        model = Company
        fields = '__all__'

class EventSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    assigned_staff = UserSerializer(many=True, read_only=True)
    class Meta:
        model = Event
        fields = '__all__'