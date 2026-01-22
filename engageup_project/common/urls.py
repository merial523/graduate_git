from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),  # トップページ用
    path("base",views.BaseTemplateMixin,name = "base_template"),
]