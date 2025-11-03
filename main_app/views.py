# backend/main_app/views.py
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import UserProfile, Company, Event
from .serializers import (
    UserSerializer,
    UserProfileSerializer,
    CompanySerializer,
    EventSerializer
)


# 1. Sign Up

class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

            # أنشئ UserProfile تلقائيًا (role = staff)
            UserProfile.objects.update_or_create(
                user=user,
                defaults={'role': 'staff', 'is_available': True}
            )

            refresh = RefreshToken.for_user(user)
            data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data,
                'role': 'staff'
            }
            return Response(data, status=status.HTTP_201_CREATED)
        except Exception as err:
            return Response({'error': str(err)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 2. Login
class LoginView(APIView):
    def post(self, request):
        try:
            username = request.data.get("username")
            password = request.data.get("password")
            if not username or not password:
                return Response({"error": "Username and password required"}, status=400)

            user = authenticate(username=username, password=password)
            if not user:
                return Response({"error": "Invalid Credentials"}, status=401)

            # تحقق من وجود UserProfile (لأنه يُنشأ في Sign Up)
            try:
                profile = UserProfile.objects.get(user=user)
                role = profile.role
            except UserProfile.DoesNotExist:
                return Response({"error": "User profile not found. Please sign up first."}, status=400)

            tokens = RefreshToken.for_user(user)
            return Response({
                "refresh": str(tokens),
                "access": str(tokens.access_token),
                "user": UserSerializer(user).data,
                "role": role
            }, status=200)
        except Exception as err:
            return Response({'error': str(err)}, status=500)


# 3. Verify Token
class VerifyUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            profile = UserProfile.objects.get(user=user)
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data,
                'role': profile.role
            }, status=status.HTTP_200_OK)
        except Exception as err:
            return Response({"error": str(err)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 4. Profile List
class ProfileList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profiles = UserProfile.objects.all()
        serializer = UserProfileSerializer(profiles, many=True)
        return Response(serializer.data)


# 5. Company CRUD
class CompanyListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        companies = Company.objects.all()
        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CompanySerializer(data=request.data)
        if serializer.is_valid():
            try:
                profile = UserProfile.objects.get(user=request.user)
            except UserProfile.DoesNotExist:
                return Response({'error': 'User profile not found'}, status=400)
            company = serializer.save(created_by=profile)
            return Response(CompanySerializer(company).data, status=201)
        return Response(serializer.errors, status=400)


# 6. Event CRUD
class EventListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = Event.objects.all()
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


# --- /profiles/me/ ---
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
        try:
            profile = UserProfile.objects.get(id=pk)  
        except UserProfile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)
        
        if request.user.profile.role != 'admin':
            return Response({"error": "Admin only"}, status=403)
        
        profile.role = request.data.get('role', profile.role)
        profile.save()
        return Response(UserProfileSerializer(profile).data)