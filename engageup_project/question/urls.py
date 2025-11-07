from django.urls import path
from . import views

urlpatterns = [
    path("", views.questions_index, name="questionIndex"),  # トップページ用
]
