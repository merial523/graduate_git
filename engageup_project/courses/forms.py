from django.db import models
from django.views.generic import ListView,UpdateView
from main.models import Course

# Create your models here.
class CourseListView(ListView):
    class Meta:
        model = Course
        fields = ['subject', 'course_count','is_mylist']