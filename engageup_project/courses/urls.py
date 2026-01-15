from django.urls import path
from . import views

urlpatterns = [
    path("", views.courses_index, name="coursesIndex"),  # トップページ用
    path(
        "text_upload", views.courses_text_upload, name="coursesTextUpload"
    ),  # 動画テキストアップロード
]
