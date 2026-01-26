from django.urls import path
from . import views

app_name = 'enrollments' 

urlpatterns = [
    path("exam_history/", views.EnrollmentsHistoryView.as_view(), name="enrollmentsHistory"),
    path('exams/', views.ExamListView.as_view(), name='exam_list'),
    path('exams/add/', views.ExamCreateView.as_view(), name='exam_add'),
    path('exam/<int:pk>/edit/', views.ExamUpdateView.as_view(), name='exam_edit'),
    path('exam/<int:exam_id>/delete/', views.ExamDeleteView.as_view(), name='exam_delete'),
    path('exam/<int:exam_id>/restore/', views.ExamRestoreView.as_view(), name='exam_restore'),
    path('exams/bulk-action/', views.ExamBulkActionView.as_view(), name='bulk_action_exam'),
    path('exam/<int:exam_id>/questions/', views.QuestionListView.as_view(), name='question_list'),
    path('exams/<int:exam_id>/question/add/', views.QuestionAddView.as_view(), name='add_question'),
    path('question/<int:question_id>/edit/', views.QuestionEditView.as_view(), name='edit_question'),
    path('question/<int:question_id>/delete/', views.QuestionDeleteView.as_view(), name='delete_question'),
    path('exam/<int:exam_id>/ai_add/', views.AddQuestionAIView.as_view(), name='exam_ai_add'),
    path('exam_list/', views.UserExamListView.as_view(), name='exam_list_user'),
    path('exam/<int:exam_id>/take/', views.ExamTakeView.as_view(), name='exam_take'),
    path('exam/<int:exam_id>/grade/', views.ExamGradeView.as_view(), name='exam_grade'),
    path('exams/<int:exam_id>/toggle-active/', views.ExamToggleActiveView.as_view(), name='exam_toggle_active'),
]
