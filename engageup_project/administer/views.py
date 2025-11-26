from django.shortcuts import render,redirect
from django.views.generic import ListView
from main.models import User
from .forms import UserRankForm

class EmployeeListView(ListView):
    model = User
    context_object_name = 'employees'
    template_name = 'administer/1104.html'
    paginate_by = 10  # ページネーションを使いたいとき


def administer_index(request):
    return render(request,"administer/administer_index.html")


def select_rank(request):
    if request.method == 'POST':
        form = UserRankForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()  # rank を保存
            return redirect('success_page')  # 遷移先
    else:
        form = UserRankForm(instance=request.user)

    return render(request, 'accounts/1104.html', {'form': form})