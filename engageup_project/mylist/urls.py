from django.urls import path
from . import views

app_name = "mylist"

urlpatterns = [
    # マイリスト一覧画面
    path("index/mylist", views.mylist_index, name="mylistIndex"),
]
