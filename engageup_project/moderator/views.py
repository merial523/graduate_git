from django.shortcuts import render
from django.views.generic import FormView, ListView, UpdateView
from django.urls import reverse_lazy
from django.db import transaction
from django.utils.crypto import get_random_string
from main.models import User
from .forms import SequentialUserCreateForm
from main.models import Badge

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
from main.models import User, Constant
from .forms import SequentialUserCreateForm


class SequentialUserCreateView(FormView):
    template_name = "moderator/mo_create_user.html"
    form_class = SequentialUserCreateForm
    success_url = reverse_lazy("moderator:moderator_index")

    PASSWORD_LENGTH = 12
    PASSWORD_CHARS = (
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    )

    def generate_password(self):
        return get_random_string(
            length=self.PASSWORD_LENGTH, allowed_chars=self.PASSWORD_CHARS
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

            # 🔑 後で表示・保存したい場合に一時的に保持
            user._raw_password = raw_password
            users.append(user)
            # ここにメールアドレスに初期パスワードを付けて送信する

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
