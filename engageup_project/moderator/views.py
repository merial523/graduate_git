from django.shortcuts import redirect, render
from django.views.generic import FormView, ListView, UpdateView
from django.urls import reverse_lazy
from django.db import transaction
from django.utils.crypto import get_random_string
from main.models import User
from .forms import SequentialUserCreateForm
from main.models import Badge
from common.views import BaseCreateView

# Create your views here.


def moderator_index(request):
    return render(request, "moderator/moderator_index.html")


def moderator_badge(request):
    return render(request, "moderator/mo_badge.html")


def moderator_news(request):
    return render(request, "moderator/mo_news.html")


# アカウントを作成する
# アカウント作成のクラスを作成する

# 仕様は会社のメールアドレスをテキスト　と　数字　の二つで構成されていると考え、数字を一つずつ増やしていき、それらにパスワードを振る


from django.views.generic import FormView
from django.urls import reverse_lazy
from django.db import transaction
from django.utils.crypto import get_random_string
from main.models import User, Constant,News
from .forms import SequentialUserCreateForm,NewsForm
from accounts.authority import AuthoritySet


class SequentialUserCreateView(FormView):
    template_name = "moderator/mo_create_user.html"
    form_class = SequentialUserCreateForm

    PASSWORD_LENGTH = 12
    PASSWORD_CHARS = (
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    )

    def get_success_url(self):
        return AuthoritySet.authority_two("administer","administer_index","moderator","moderator_index",self.request.user.rank)

    def generate_password(self):
        return get_random_string(
            length=self.PASSWORD_LENGTH,
            allowed_chars=self.PASSWORD_CHARS
        )

    def form_valid(self, form):
        company_code = Constant.objects.values_list("company_code", flat=True).first()
        start_number = form.cleaned_data["start_number"]
        count = form.cleaned_data["count"]
        rank = form.cleaned_data["rank"]
        email_address = Constant.objects.values_list("address", flat=True).first()

        users = []

        for i in range(count):
            number = start_number + i
            username = f"user{number}"
            email = f"{company_code}{number}@{email_address}"

            if User.objects.filter(username=username).exists():
                form.add_error(None, f"{username} は既に存在します")
                return self.form_invalid(form)

            raw_password = self.generate_password()
            user = User(username=username, email=email, rank=rank)
            user.set_password(raw_password)

            user._raw_password = raw_password
            users.append(user)

        with transaction.atomic():
            User.objects.bulk_create(users)

        return super().form_valid(form)


class BadgeManageView(ListView):
    model = Badge
    template_name = "moderator/mo_badge.html"
    context_object_name = "badges"

    def get_queryset(self):
        query = self.request.GET.get("q")
        if query:
            return Badge.objects.filter(name__icontains=query)
        return Badge.objects.all()


class BadgeUpdateView(UpdateView):
    model = Badge
    fields = ["name", "icon", "exam"]
    template_name = "moderator/mo_badge_update.html"
    success_url = reverse_lazy("moderator:moderatorBadge")

#管理者HTMLで入力したテキストを一般会員HTMLで見れるようにする

class NewsListView(ListView):
    model = News
    template_name = "moderator/mo_news_list.html"
    context_object_name = "news_"
    paginate_by = 10

    def get_queryset(self):
        show = self.request.GET.get("show")

        if show == "deleted":
            return News.objects.filter(is_active=False).order_by("id")

        return News.objects.filter(is_active=True).order_by("id")

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        ids = request.POST.getlist("news_ids")

        if ids:
            if action == "delete":
                News.objects.filter(id__in=ids).update(is_active=False)

            elif action == "restore":
                News.objects.filter(id__in=ids).update(is_active=True)

        return redirect(request.get_full_path())


class NewsCreateView(BaseCreateView):
    model = News
    form_class = NewsForm
    template_name = "moderator/mo_news_form.html"
    success_url = reverse_lazy("moderator:news_list")

    def form_valid(self, form):
        form.instance.is_active = True
        return super().form_valid(form)

class NewsUpdateView(UpdateView):
    model = News
    form_class = NewsForm
    template_name = "moderator/mo_news_form.html"
    success_url = reverse_lazy("moderator:news_list")

    def get_queryset(self):
        return News.objects.filter(is_active=True)
