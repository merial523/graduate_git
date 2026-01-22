from django.urls import path
from . import views

app_name = "staff"

urlpatterns = [
    path("", views.StaffIndex.as_view(), name="staff_index"),  # トップページ用
    path("staff-list",views.UserListView.as_view(),name = "staff_list"),
]
