from django.urls import path
from . import views

urlpatterns = [
    path(
        "ai_question/", views.aiQuestion_Index, name="aiQuestionIndex"
    ),  # トップページ用
]
