from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView, UpdateView,CreateView


def index(request):
    return render(
        request, "common/index.html"
    )  # アプリ内 templates/common/index.html を参照

#共通で返す処理
class BaseCreateView(CreateView):
    is_continue = None      #続けて保存か判定
    is_continue_url = ""    #送信先のURL
    #権限を分ける関数　
    def get_success_url(self):
        if self.is_continue:
            return reverse_lazy(self.is_continue_url)
        rank = self.request.user.rank
        if rank == "administer":
            return reverse_lazy("administer:administer_index")
        elif rank == "moderator":
            return reverse_lazy("moderator:moderator_index")
        elif rank == "staff":
            return reverse_lazy("staff:staff_index")
        elif rank == "vistor":
            return reverse_lazy("vistor:vistor_index")