from django.urls import path
from . import views

app_name = "moderator"
urlpatterns = [
    path("", views.moderator_index, name="moderator_index"),  # トップページ用
    path(
        "create-user",
        views.SequentialUserCreateView.as_view(),
        name="moderator_create_user",
    ),  # ユーザーを作成する
    path(
        "moderator_badge/", views.moderator_badge, name="moderatorBadge"
    ),  # バッジ管理ページ
    path(
        "moderator_news/", views.moderator_news, name="moderatorNews"
    ),  # お知らせ投稿ページ
]
