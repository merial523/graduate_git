from django.shortcuts import render
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from .forms import UserUpdateForm
from main.models import User


def visitor_indexindex(request):
    return render(request, "visitor/visitor_index.html")
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from django.http import HttpResponseRedirect
from django.contrib.auth import logout

class UserUpdateView(UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = "visitor/visitor_update.html"
    success_url = reverse_lazy("accounts:logout")


    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        user = form.save(commit=False)

        # パスワード変更
        user.set_password(form.cleaned_data["password"])

        # ランク自動昇格
        if user.rank == "visitor":
            user.rank = "staff"

        user.save()

        # UpdateViewに「保存済み」を伝える
        self.object = user

        # ログアウトしてログイン画面へ
        logout(self.request)
        return HttpResponseRedirect(self.get_success_url())
