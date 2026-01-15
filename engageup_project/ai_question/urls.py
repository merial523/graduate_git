from django.urls import path
from . import views

urlpatterns = [
    path("", views.ai_question_index, name="aiQuestionIndex"),  # トップページ用
    path(
        "ai_question/", views.aiQuestion_Index, name="aiQuestionIndex"
    ),  # トップページ用
]
