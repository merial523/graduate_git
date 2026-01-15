from django.urls import path
from . import views

app_name = "courses"

urlpatterns = [
    path("", views.courses_index, name="coursesIndex"),
    path("course-list", views.CourseListView.as_view(), name="courses_list"),
    path("course-create", views.CourseCreateView.as_view(), name="courses_create"),
    path("course-update/<int:pk>", views.CourseUpdateView.as_view(), name="courses_update"),
]
