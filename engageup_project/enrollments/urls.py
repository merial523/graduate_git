from django.urls import path
from . import views

app_name = 'enrollments' 


urlpatterns = [
    # --- 基本・トップ ---
    path("", views.EnrollmentsIndexView.as_view(), name="enrollmentsIndex"),
    path("exam_history/", views.EnrollmentsHistoryView.as_view(), name="enrollmentsHistory"),

    # --- 検定管理（管理者用） ---
    path('exams/', views.ExamListView.as_view(), name='exam_list'),
    path('exams/add/', views.ExamCreateView.as_view(), name='exam_add'),
    path('exam/<int:pk>/edit/', views.ExamUpdateView.as_view(), name='exam_edit'),
    path('exam/<int:exam_id>/delete/', views.delete_exam, name='exam_delete'),
    
    # 復元（論理削除したものを戻す）
    path('exam/<int:exam_id>/restore/', views.restore_exam, name='exam_restore'),
    
    path('exams/bulk_action/', views.bulk_action_exam, name='bulk_action_exam'),

    # --- 問題管理 ---
    path('exam/<int:exam_id>/questions/', views.question_list, name='question_list'),
    path('exams/<int:exam_id>/question/add/', views.add_question, name='add_question'),
    path('question/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('question/<int:question_id>/delete/', views.delete_question, name='delete_question'),

    # --- AI自動生成 ---
    path('exam/<int:exam_id>/ai_add/', views.add_question_ai, name='exam_ai_add'),

    # --- 受験・採点（受講者用） ---
    path('exam_list/', views.user_exam_list, name='exam_list_user'),
    path('exam/<int:exam_id>/take/', views.exam_take, name='exam_take'),
    path('exam/<int:exam_id>/grade/', views.exam_grade, name='exam_grade'),
]
