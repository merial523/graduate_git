from django.urls import path
from . import views

app_name = "visitor"

urlpatterns = [
    path("", views.visitor_indexindex, name="visitor_index"),  # トップページ用
    path("visitor/<int:pk>/update/", views.UserUpdateView.as_view(),name = "visitor_update")# アップデート
]
