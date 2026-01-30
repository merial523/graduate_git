from django.urls import path
from . import views
from administer.views import UserListView

app_name = "moderator"
urlpatterns = [
    path("", views.ModeratorIndexView.as_view(), name="moderator_index"),  # トップページ用
    path("create-user", views.SequentialUserCreateView.as_view(), name="moderator_create_user"),
    
    # ユーザーを作成する
    path("user-list/", UserListView.as_view(), name="user_list"),

    # バッジ管理一覧画面
    path("badges/", views.BadgeManageView.as_view(), name="moderatorBadge"),

    # バッジ編集画面
    path("badges/<int:pk>/edit/", views.BadgeUpdateView.as_view(), name="badge_edit"),
    path("moderator_news/", views.ModeratorNewsView.as_view(), name="moderatorNews"),  

    # お知らせ投稿ページ
    path("news-list",views.NewsListView.as_view(),name ="news_list"),
    path("news-create",views.NewsCreateView.as_view(),name = "news_create"),
    path('news-update/<int:pk>/', views.NewsUpdateView.as_view(), name='news_update'),
    path('news-toggle-active/<int:pk>/', views.NewsToggleActiveView.as_view(), name='news_toggle_active'),
    path('news-bulk-action/', views.NewsBulkActionView.as_view(), name='news_bulk_action'),
    path('news-delete/<int:pk>/', views.NewsDeleteView.as_view(), name='news_delete'),
    path(
    "check-user-duplicate/",
    views.check_user_duplicate,
    name="check_user_duplicate"
),

]
