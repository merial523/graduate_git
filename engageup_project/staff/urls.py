from django.urls import path
from . import views
app_name = "staff"

app_name = "staff"

urlpatterns = [
    path("staff-list",views.UserListView.as_view(),name = "staff_list"),
    path("", views.StaffIndex.as_view(), name="staff_index"),  # スタッフ用トップページ用
    path("news/", views.StaffNewsListView.as_view(), name="news_list"),  # お知らせ一覧ページ用
]
