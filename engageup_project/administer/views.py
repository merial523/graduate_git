from django.shortcuts import render,redirect
from django.views.generic import ListView
from main.models import User
from .forms import UserRankForm

def administer_index(request):
    return render(request,"administer/administer_index.html")


class UserListView(ListView):
    model = User
    context_object_name = 'users'
    template_name = 'administer/1104.html'
    pagenate_by = 10
    def get(self, request):
        users = User.objects.all()
        form = UserRankForm()
        return render(request, self.template_name, {'users': users, 'form': form})
