from django.shortcuts import render


def index(request):
    return render(
        request, "main/index.html"
    )  # アプリ内 templates/main/index.html を参照
