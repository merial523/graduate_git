from django.shortcuts import render


# Create your views here.
def profile_index(request):
    return render(request, "profile/2101.html")
