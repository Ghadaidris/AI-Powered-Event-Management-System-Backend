from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Auth
    path('signup/', views.CreateUserView.as_view()),
    path('login/', views.LoginView.as_view()),
    path('verify/', views.VerifyUserView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Profiles
    path('profiles/', views.ProfileList.as_view()),
    path('profiles/<int:pk>/', views.ProfileDetail.as_view()),
    path('profiles/me/', views.get_me),

    # Companies
    path('companies/', views.CompanyListCreate.as_view()),
    path('companies/<int:pk>/', views.CompanyDetail.as_view()),

    # Events
    path('events/', views.EventListCreate.as_view()),
    path('events/<int:pk>/', views.EventDetail.as_view()),

    # Teams
    path('teams/', views.TeamListCreate.as_view(), name='team-list'),
    path('teams/<int:pk>/', views.TeamDetail.as_view(), name='team-detail'),

    # Tasks
    path('tasks/', views.TaskListCreate.as_view()),
    path('tasks/<int:pk>/', views.TaskDetail.as_view()),
    path('tasks/<int:pk>/split-ai/', views.TaskSplitAI.as_view(), name='task-split-ai'),
    path('manager/teams/', views.ManagerTeamList.as_view()),
    path('manager/tasks/', views.ManagerTaskList.as_view()),

    # Missions
    path('missions/', views.MissionListCreate.as_view(), name='mission-list'),
    path('missions/<int:pk>/', views.MissionDetail.as_view(), name='mission-detail'),

    #  New Manager Workflow Endpoints
    path('missions/<int:pk>/ai_assign/', views.MissionAssignAI.as_view(), name='mission-ai-assign'),
    path('missions/<int:pk>/approve/', views.ManagerApproveTasks.as_view(), name='mission-approve'),

    path('teams/<int:pk>/add-member/', views.AddTeamMember.as_view(), name='add-team-member'),

]
