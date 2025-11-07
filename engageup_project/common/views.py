from django.shortcuts import render


def index(request):
    return render(
        request, "common/index.html"
    )  # アプリ内 templates/common/index.html を参照
