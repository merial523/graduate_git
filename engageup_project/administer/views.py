from django.shortcuts import render, redirect
from django.views.generic import ListView
from main.models import User
from .forms import UserRankForm

def administer_index(request):
    return render(request, "administer/administer_index.html")


class UserListView(ListView):
    model = User
    context_object_name = 'users'
    template_name = 'administer/1104.html'
    paginate_by = 10  # ← スペル修正

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = UserRankForm()
        return context

    def post(self, request, *args, **kwargs):
        selected_users = request.POST.getlist('selected_user')
        form = UserRankForm(request.POST)

        if selected_users and form.is_valid():
            new_rank = form.cleaned_data['rank']

            users = User.objects.filter(pk__in=selected_users)

            for user in users:
                # ★ 自分自身はスキップ
                if user == request.user:
                    continue

                user.rank = new_rank
                user.save()

        return redirect('select_rank')
