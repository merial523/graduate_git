from django.urls import path
from . import views

urlpatterns = [
    path("", views.enrollments_index, name="enrollmentsIndex"),  # トップページ用
    path(
        "exam_history", views.enrollments_history, name="enrollmentsHistory"
    ),  # 検定履歴
    path(
        "exam_create", views.enrollments_create, name="enrollmentsCreate"
    ),  # 検定問題作成
]
