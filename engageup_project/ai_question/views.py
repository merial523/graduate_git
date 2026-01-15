from django.shortcuts import render

# Create your views here.

def ai_question_index(request):
    return render(request, "ai_question/ai_question_index.html")

