from django.urls import path
from . import views

app_name = "news"
urlpatterns = [
    path("news-create",views.NewsCreateView.as_view(),name= "news_create"),
    path("news-history",views.NewsListView.as_view(),name = "news_history"),
    path('news/<int:news_id>/delete/', views.NewsDeleteView.as_view(), name='news_delete'),
]
