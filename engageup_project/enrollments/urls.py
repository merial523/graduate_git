from django.urls import path
from . import views

urlpatterns = [
    path("", views.enrollments_index, name="enrollmentsIndex"),  # トップページ用
]
