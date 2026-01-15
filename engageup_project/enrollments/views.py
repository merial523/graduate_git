from django.shortcuts import render


# Create your views here.
def enrollments_index(request):
    return render(
        request, "enrollments/5101.html"
    )  # アプリ内 templates/enrollments/index.html を参照


def enrollments_create(request):
    return render(
        request, "enrollments/mo_exam_create.html"
    )  # アプリ内 templates/enrollments/index.html を参照


def enrollments_history(request):
    return render(
        request, "enrollments/history_exam.html"
    )  # アプリ内 templates/enrollments/index.html を参照
