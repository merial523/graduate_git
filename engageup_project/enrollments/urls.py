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

    # 特定の検定の問題一覧を見る
    path('exam/<int:exam_id>/questions/', views.question_list, name='question_list'),
    
    # 特定の問題を編集する
    path('question/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    
    # 特定の問題を削除する（おまけ）
    path('question/<int:question_id>/delete/', views.delete_question, name='delete_question'),

    path('exam/<int:exam_id>/ai_add/', views.add_question_ai, name='exam_ai_add'), # AIによる問題追加

]
