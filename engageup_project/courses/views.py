from django.shortcuts import render


# Create your views here.
def courses_index(request):
    return render(request, "Courses/4101.html")
