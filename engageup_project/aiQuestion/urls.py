from django.urls import path
from . import views

urlpatterns = [
    path("", views.aiQuestion_index, name="aiQuestionIndex"),  # トップページ用
]
