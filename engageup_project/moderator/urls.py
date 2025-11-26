from django.urls import path
from . import views

urlpatterns = [
    path("", views.moderator_indexindex, name="moderator_index"),  # トップページ用
]
