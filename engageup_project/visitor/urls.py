from django.urls import path
from . import views

urlpatterns = [
    path("", views.visitor_indexindex, name="visitor_index"),  # トップページ用
    path("visitor/<int:pk>/update/", views.)
]
