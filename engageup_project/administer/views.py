from django.shortcuts import redirect
from django.urls import reverse_lazy

from django.utils.crypto import get_random_string

from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.conf import settings
from django.shortcuts import redirect
from django.views.generic import (
    TemplateView,
    ListView,
    UpdateView,
)
from django.db.models import Q

from main.models import User, Constant
from .forms import UserRankForm, ConstantForm
from common.views import AdminOrModeratorRequiredMixin, BaseTemplateMixin


# =========================
# トップ
# =========================
class AdministerIndexView(
    AdminOrModeratorRequiredMixin,
    BaseTemplateMixin,
    TemplateView
):
    template_name = "administer/administer_index.html"


# =========================
# ユーザー一覧
# =========================
class UserListView(
    AdminOrModeratorRequiredMixin,
    BaseTemplateMixin,
    ListView
):
    model = User
    template_name = "administer/ad_user_list.html"
    context_object_name = "users"
    paginate_by = 10

    def get_queryset(self):
        show = self.request.GET.get("show")
        query = self.request.GET.get("q")
        rank_filter = self.request.GET.get("rank")

        queryset = (
            User.objects.all()
            if show == "all"
            else User.objects.filter(is_active=True)
        )

        if rank_filter and rank_filter != "all":
            queryset = queryset.filter(rank=rank_filter)

        if query:
            queryset = queryset.filter(
                Q(username__icontains=query) |
                Q(email__icontains=query)
            )

        return queryset.order_by("-pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["rank_choices"] = [
            "administer",
            "moderator",
            "staff",
            "visitor",
        ]
        context["current_rank"] = self.request.GET.get("rank", "all")
        context["show_all"] = self.request.GET.get("show") == "all"
        return context

    def post(self, request, *args, **kwargs):
        # Admin のみ実行可能
        if request.user.rank != "administer":
            return redirect(request.path)

        action = request.POST.get("action")
        selected_users = request.POST.getlist("selected_user")

        if selected_users:
            if action == "soft_delete":
                User.objects.filter(
                    pk__in=selected_users
                ).exclude(
                    pk=request.user.pk
                ).update(is_active=False)

            elif action == "restore":
                User.objects.filter(
                    pk__in=selected_users
                ).update(is_active=True)

        return redirect(request.path)


# =========================
# ユーザーランク一覧
# =========================
class UserRankListView(
    AdminOrModeratorRequiredMixin,
    BaseTemplateMixin,
    ListView
):
    model = User
    template_name = "administer/ad_select_rank.html"
    context_object_name = "users"
    paginate_by = 10

    def get_queryset(self):
        queryset = User.objects.all()

        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(username__icontains=query) |
                Q(email__icontains=query)
            )

        rank_filter = self.request.GET.get("rank_filter")
        if rank_filter and rank_filter != "all":
            queryset = queryset.filter(rank=rank_filter)

        return queryset.order_by("-pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["rank_choices"] = [
            "administer",
            "moderator",
            "staff",
            "visitor",
        ]
        context["current_rank"] = self.request.GET.get(
            "rank_filter",
            "all"
        )
        context["form"] = UserRankForm()
        return context


    def post(self, request, *args, **kwargs):
        selected_users = request.POST.getlist("selected_user")
        form = UserRankForm(request.POST)

        if selected_users and form.is_valid():
            new_rank = form.cleaned_data["rank"]
            users = User.objects.filter(pk__in=selected_users)

            for user in users:
                if user == request.user:
                    continue

                user.rank = new_rank

                # visitor に変更された場合のみ
                if new_rank == "visitor":
                    raw_password = get_random_string(12)

                    # 🔐 Django標準のパスワード更新
                    user.set_password(raw_password)
                    user.save()

                    # ✉️ Django標準のメール送信
                    send_mail(
                        subject="【重要】ログイン情報のお知らせ",
                        message=f"""
    {user.username} 様

    ランク変更により、パスワードが再発行されました。

    ログイン情報
    --------------------
    ユーザー名：{user.username}
    パスワード：{raw_password}
    --------------------

    ※ログイン後、必ずパスワードを変更してください。
    """,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=False,
                    )
                else:
                    user.save()

        return redirect("administer:select_rank")

# =========================
# 定数リスト
# =========================
class ConstantListView(
    AdminOrModeratorRequiredMixin,
    BaseTemplateMixin,
    ListView
):
    model = Constant
    template_name = "administer/ad_constant_list.html"
    context_object_name = "constants"
    paginate_by = 10


# =========================
# 定数変更
# =========================
class ConstantUpdateView(
    AdminOrModeratorRequiredMixin,
    BaseTemplateMixin,
    UpdateView
):
    model = Constant
    form_class = ConstantForm
    template_name = "administer/ad_constant_update.html"
    success_url = reverse_lazy("administer:constant_list")

    def get_object(self, queryset=None):
        return Constant.objects.first()
