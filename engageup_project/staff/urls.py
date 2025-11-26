from django.urls import path
from . import views

urlpatterns = [
    path("", views.staff_indexindex, name="staff_index"),  # トップページ用
]
