from django.urls import path
from . import views

app_name = "moderator"
urlpatterns = [
    path("", views.ModeratorIndexView.as_view(), name="moderator_index"),  # トップページ用
    path(
        "create-user",
        views.SequentialUserCreateView.as_view(),
        name="moderator_create_user",
    ),  # ユーザーを作成する
    # バッジ管理一覧画面
    # reverse_lazy("moderator:moderatorBadge") と対応させる
    path("badges/", views.BadgeManageView.as_view(), name="moderatorBadge"),
    # バッジ編集画面
    # <int:pk> はバッジのID（数字）が入ります。HTMLの url 'moderator:badge_edit' と対応
    path("badges/<int:pk>/edit/", views.BadgeUpdateView.as_view(), name="badge_edit"),
    path(
        "moderator_news/", views.ModeratorNewsView.as_view(), name="moderatorNews"
    ),  # お知らせ投稿ページ

    path("news-list",views.NewsListView.as_view(),name ="news_list"),
    path("news-create",views.NewsCreateView.as_view(),name = "news_create"),
    path("news-update",views.NewsUpdateView.as_view(),name = "news_update"),

]
