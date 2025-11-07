from django.shortcuts import render

# Create your views here.
def questions_index(request):
    return render(request, "question/6101.html")
