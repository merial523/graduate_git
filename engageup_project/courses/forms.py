from django import forms
from main.models import Course

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["subject", "courseCount", "is_mylist"]
