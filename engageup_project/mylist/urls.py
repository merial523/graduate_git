from django.urls import path
from . import views
from mylist.views import MylistIndexView

app_name = "mylist"

urlpatterns = [
    # マイリスト一覧画面
    path("index/mylist", MylistIndexView.as_view(), name="mylistIndex"),
]