from django.urls import path
from . import views

app_name = "prof"

urlpatterns = [
    path('my-profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
]
