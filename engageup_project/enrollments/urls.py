from django.urls import path
from . import views

app_name = 'enrollments'  # ← ★これが必要です！


urlpatterns = [
    path("", views.enrollments_index, name="enrollmentsIndex"),  # トップページ用
    path(
        "exam_history", views.enrollments_history, name="enrollmentsHistory"
    ),  # 検定履歴

        # 検定一覧
    path('exams/', views.ExamListView.as_view(), name='exam_list'),
    # 検定作成
    path('exams/add/', views.ExamCreateView.as_view(), name='exam_add'),
    # 問題追加
    path('exams/<int:exam_id>/question/add/', views.add_question, name='add_question'),

]
