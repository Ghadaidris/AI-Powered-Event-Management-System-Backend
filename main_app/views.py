
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import UserProfile, Company, Event
from .serializers import UserSerializer, UserProfileSerializer, CompanySerializer, EventSerializer


#Sign Up (للـ Staff فقط - سيُستخدم)
class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            
            # أنشئ UserProfile تلقائيًا (role = staff)
            UserProfile.objects.create(user=user, role='staff')
            
            refresh = RefreshToken.for_user(user)
            data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            }
            return Response(data, status=status.HTTP_201_CREATED)
        except Exception as err:
            return Response({'error': str(err)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

            try:
                profile = UserProfile.objects.get(user=user)
                role = profile.role
            except UserProfile.DoesNotExist:
                return Response({"error": "User profile not found."}, status=400)

            tokens = RefreshToken.for_user(user)
            return Response({
                "refresh": str(tokens),  
                "access": str(tokens.access_token),
                "user": UserSerializer(user).data,
                "role": role
            }, status=200)
        except Exception as err:
            return Response({'error': str(err)}, status=500)
        
# 3. Verify Token ( - للـ Frontend)
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