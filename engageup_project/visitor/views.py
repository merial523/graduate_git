from django.shortcuts import render

# Create your views here.


def visitor_index(request):
    return render(request,"visitor/visitor_index.html")