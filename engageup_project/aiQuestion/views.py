from django.shortcuts import render

# Create your views here.
def aiQuestion_index(request):
    return render(request, "aiQuestion/aiQuestion.html")
