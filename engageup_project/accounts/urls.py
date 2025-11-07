from django.urls import path
from . import views

urlpatterns = [
    path("", views.accounts_index, name="accountsIndex"),  # トップページ用
]
