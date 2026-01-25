from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # 管理側
    path('', views.CoursesIndexView.as_view(), name='courseIndex'),
    path('list/', views.CourseListView.as_view(), name='courses_list'),
    path('add/', views.CourseCreateView.as_view(), name='courses_add'),
    path('<int:pk>/edit/', views.CourseUpdateView.as_view(), name='courses_edit'),
    path('module/<int:module_id>/delete/', views.TrainingModuleDeleteView.as_view(), name='module_delete'),
    path('bulk-action/', views.CourseBulkActionView.as_view(), name='bulk_action_course'),
    
    # 管理側：研修モジュール
    path('<int:course_id>/module/add/', views.TrainingModuleCreateView.as_view(), name='module_add'),
    path('module/<int:pk>/edit/', views.TrainingModuleUpdateView.as_view(), name='module_edit'),
    path('module/<int:module_id>/restore/', views.TrainingModuleRestoreView.as_view(), name='module_restore'),
    
    
    # 管理側：AI自動生成機能
    path('module/<int:module_id>/ai-full-generate/', views.TrainingAllAutoGenerateView.as_view(), name='ai_full_generate'),

    # 受講者側
    path('staff/list/', views.StaffCourseListView.as_view(), name='staff_course_list'),
    path('staff/training/<int:module_id>/', views.StaffTrainingDetailView.as_view(), name='training_detail'),
]