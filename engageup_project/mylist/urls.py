from django.urls import path
from . import views

urlpatterns = [
    path("", views.mylist_index, name="mylistIndex"),  # トップページ用
]
