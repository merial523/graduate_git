from django.urls import path
from . import views

urlpatterns = [
    path("", views.profile_index, name="profileIndex"),  # トップページ用
]
