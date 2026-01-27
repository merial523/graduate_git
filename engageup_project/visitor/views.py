from django.shortcuts import render
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from .models import User


# Create your views here.


def visitor_index(request):
    return render(request,"visitor/visitor_index.html")


class UserUpdateView(UpdateView):
    model = User
    fields = ["username","password"]
    template_name = "user/user_update.html"
    success_url = reverse_lazy("user_list")
