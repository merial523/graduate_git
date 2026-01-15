from django.urls import path
from . import views

app_name = "courses"
urlpatterns = [
    path("", views.courses_index, name="coursesIndex"),  # トップページ用
    path(
        "text_upload", views.courses_text_upload, name="coursesTextUpload"
    ),  # 動画テキストアップロード
    path("course-list", views.CourseListView.as_view(), name="couses_list"),  # コース表示一覧
]
