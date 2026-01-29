from django.urls import path
from . import views

urlpatterns = [
    path("", views.mylist_index, name="mylistIndex"),  # トップページ用
    path("news/<int:news_id>/favorite/", views.add_favorite_news, name="add_favorite_news"),
    path("news/<int:news_id>/unfavorite/", views.remove_favorite_news, name="remove_favorite_news"),

]
