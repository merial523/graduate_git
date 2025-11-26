from django.shortcuts import render

# Create your views here.

def moderator_index(request):
    return render(request,"moderator/moderator_index.html")