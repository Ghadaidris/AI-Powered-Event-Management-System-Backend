
from django.urls import path
from .views import ProfileList, CompanyListCreate, EventListCreate, CreateUserView, LoginView
from . import views

urlpatterns = [
    path('signup/', views.CreateUserView.as_view()),
    path('login/', views.LoginView.as_view()),
    path('verify/', views.VerifyUserView.as_view()),
    path('profiles/', views.ProfileList.as_view()),
    path('companies/', views.CompanyListCreate.as_view()),
    path('events/', views.EventListCreate.as_view()),
]