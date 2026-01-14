from django.shortcuts import render


# Create your views here.
def aiQuestion_Index(request):
    return render(request, "ai_question/aiQuestion_index.html")
