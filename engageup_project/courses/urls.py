from django.urls import path
from . import views

app_name = "courses"

urlpatterns = [
    # ==============================
    #  管理側（コース・モジュール管理）
    # ==============================
    path("", views.CoursesIndexView.as_view(), name="courseIndex"),
    path("list/", views.CourseListView.as_view(), name="courses_list"),
    path("add/", views.CourseCreateView.as_view(), name="courses_add"),
    path("<int:pk>/edit/", views.CourseUpdateView.as_view(), name="courses_edit"),
    path("bulk-action/", views.CourseBulkActionView.as_view(), name="bulk_action_course"),
    path("toggle_active/<int:pk>/",views.CourseToggleActiveView.as_view(),name="course_toggle_active",),
    path('module/<int:pk>/toggle/', views.TrainingModuleToggleActiveView.as_view(), name='module_toggle_active'),
    path('module/<int:module_id>/delete/', views.TrainingModuleDeleteView.as_view(), name='module_delete'),
    # 管理側：研修モジュール
    path(
        "<int:course_id>/module/add/",
        views.TrainingModuleCreateView.as_view(),
        name="module_add",
    ),
    path(
        "module/<int:pk>/edit/",
        views.TrainingModuleUpdateView.as_view(),
        name="module_edit",
    ),
    path(
        "module/<int:module_id>/delete/",
        views.TrainingModuleDeleteView.as_view(),
        name="module_delete",
    ),
    # 管理側：AI自動生成
    path(
        "module/<int:module_id>/ai-full-generate/",
        views.TrainingAllAutoGenerateView.as_view(),
        name="ai_full_generate",
    ),
    # ==============================
    #  受講者側
    # ==============================
    path("staff/list/", views.StaffCourseListView.as_view(), name="staff_course_list"),
    path(
        "staff/training/<int:module_id>/",
        views.StaffTrainingDetailView.as_view(),
        name="training_detail",
    ),
    path(
        "staff/update_video_progress/",
        views.UpdateVideoProgressView.as_view(),
        name="save_progress",
    ),
    # ==============================
    #  マイリスト機能（MyList）
    # ==============================
    # 1. マイリスト一覧画面（2枚目の画像）
    path("mylist/", views.mylist_index, name="mylist_index"),
    # 2. 講座のお気に入りトグル (Ajax)
    path(
        "mylist/toggle/<int:course_id>/",
        views.toggle_course_favorite,
        name="mylist_toggle",
    ),
    # 3. お知らせのお気に入りトグル (Ajax) ★ここを追加
    path(
        "mylist/news/toggle/<int:news_id>/",
        views.toggle_news_favorite,
        name="mylist_news_toggle",
    ),
]
