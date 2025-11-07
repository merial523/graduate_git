from django.shortcuts import render


# Create your views here.
def enrollments_index(request):
    return render(
        request, "enrollments/5101.html"
    )  # アプリ内 templates/enrollments/index.html を参照