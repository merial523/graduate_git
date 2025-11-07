from django.shortcuts import render

# Create your views here.

def ai_question_index(request):
    return render(
        request, "ai_question/3105.html"
    )  # アプリ内 templates/ai_question/index.html を参照