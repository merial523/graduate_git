from django.shortcuts import redirect
from django.views.generic import (
    TemplateView,
    FormView,
    ListView,
    UpdateView,
)
from django.urls import reverse_lazy
from django.db import transaction
from django.utils.crypto import get_random_string
from django.core.exceptions import PermissionDenied

from main.models import User, Badge, Constant, News
from .forms import SequentialUserCreateForm, NewsForm
from accounts.authority import AuthoritySet
from common.views import BaseCreateView, BaseTemplateMixin,AdminOrModeratorRequiredMixin

from django.core.cache import cache
from django.db.models import Count, Q

# =====================================================
# トップ・固定ページ
# =====================================================
class ModeratorIndexView(
    AdminOrModeratorRequiredMixin,
    BaseTemplateMixin,
    TemplateView
):
    template_name = "moderator/moderator_index.html"


class ModeratorBadgeView(
    AdminOrModeratorRequiredMixin,
    BaseTemplateMixin,
    TemplateView
):
    template_name = "moderator/mo_badge.html"


class ModeratorNewsView(
    AdminOrModeratorRequiredMixin,
    BaseTemplateMixin,
    TemplateView
):
    template_name = "moderator/mo_news.html"


# =====================================================
# アカウント連番作成
# =====================================================
from django.views.generic import FormView
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction

class SequentialUserCreateView(
    AdminOrModeratorRequiredMixin,
    BaseTemplateMixin,
    FormView
):
    template_name = "moderator/mo_create_user.html"
    form_class = SequentialUserCreateForm

    PASSWORD_LENGTH = 12
    PASSWORD_CHARS = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789!@#$%^&*"
    )

    def get_success_url(self):
        return AuthoritySet.authority_two(
            "administer", "user_list",
            "moderator", "user_list",
            self.request.user.rank
        )

    def generate_password(self):
        return get_random_string(
            length=self.PASSWORD_LENGTH,
            allowed_chars=self.PASSWORD_CHARS
        )

    def form_valid(self, form):
        company_code = Constant.objects.values_list(
            "company_code", flat=True
        ).first()
        email_address = Constant.objects.values_list(
            "address", flat=True
        ).first()

        start_number = form.cleaned_data["start_number"]
        count = form.cleaned_data["count"]
        rank = form.cleaned_data["rank"]

        users = []

        for i in range(count):
            number = start_number + i
            username = f"user{number}"
            email = f"{company_code}{number}@{email_address}"

            if User.objects.filter(username=username).exists():
                form.add_error(None, f"{username} は既に存在します")
                return self.form_invalid(form)

            raw_password = self.generate_password()
            user = User(
                username=username,
                email=email,
                rank=rank
            )
            user.set_password(raw_password)

            # メール用に一時保持
            user._raw_password = raw_password
            users.append(user)

        # DB保存
        with transaction.atomic():
            User.objects.bulk_create(users)

        # メール送信（console backendならターミナルに出る）
        for user in users:
            print(f"[MAIL DEBUG] to={user.email}")  # ← 確認用

            send_mail(
                subject="アカウント作成のお知らせ",
                message=f"""
{user.username} 様

アカウントが作成されました。

ログイン情報
ユーザー名: {user.username}
パスワード: {user._raw_password}
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

        return super().form_valid(form)

# =====================================================
# Badge 管理
# =====================================================
class BadgeManageView(
    AdminOrModeratorRequiredMixin,
    BaseTemplateMixin,
    ListView
):
    model = Badge
    template_name = "moderator/mo_badge.html"
    context_object_name = "badges"

    def get_queryset(self):
        q = self.request.GET.get("q")
        ps = Badge.objects.filter(is_active=True)
        if q:
            ps = ps.filter(name__icontains=q)
        return ps


class BadgeUpdateView(
    AdminOrModeratorRequiredMixin,
    BaseTemplateMixin,
    UpdateView
):
    model = Badge
    fields = ["name", "icon"]
    template_name = "moderator/mo_badge_update.html"
    success_url = reverse_lazy("moderator:moderatorBadge")




# =====================================================
# News 管理
# =====================================================
class NewsListView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, ListView):
    model = News
    template_name = "moderator/mo_news_list.html"
    context_object_name = "news_"
    paginate_by = 10

    def get_queryset(self):
        # パラメータ取得
        show = self.request.GET.get("show")
        q = self.request.GET.get("q")
        
        # ベースのクエリ（ID降順＝新しい順が一般的）
        qs = News.objects.order_by("-id")

        # 1. 削除済みか有効か
        is_trash = (show == "deleted")
        if is_trash:
            qs = qs.filter(is_active=False)
        else:
            qs = qs.filter(is_active=True)

        # 2. 検索機能
        if q:
            qs = qs.filter(
                Q(title__icontains=q) | Q(content__icontains=q)
            )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # テンプレート側で使う変数を渡す
        context['is_trash_mode'] = (self.request.GET.get("show") == "deleted")
        context['search_query'] = self.request.GET.get("q", "")
        # バッジ表示用のカウントなど（任意）
        context['total_active'] = News.objects.filter(is_active=True).count()
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        ids = request.POST.getlist("news_ids")

        if ids:
            qs = News.objects.filter(id__in=ids)
            if action == "delete":
                qs.update(is_active=False)
            elif action == "restore":
                qs.update(is_active=True)
            # 復元時はゴミ箱ページへリダイレクトすると親切
            if action == "restore":
                 return redirect(request.path + "?show=deleted")

        return redirect(request.path)


class NewsCreateView(
    AdminOrModeratorRequiredMixin,
    BaseTemplateMixin,
    BaseCreateView
):
    model = News
    form_class = NewsForm
    template_name = "moderator/mo_news_form.html"
    success_url = reverse_lazy("moderator:news_list")
    is_continue_url = "moderator:news_list"
    is_continue = True

    def form_valid(self, form):
        # 公開設定の初期値
        form.instance.is_active = True
        # ★追加: ログイン中のユーザーを作成者として保存
        form.instance.author = self.request.user
        return super().form_valid(form)


class NewsUpdateView(
    AdminOrModeratorRequiredMixin,
    BaseTemplateMixin,
    UpdateView
):
    model = News
    form_class = NewsForm
    template_name = "moderator/mo_news_form.html"
    success_url = reverse_lazy("moderator:news_list")

    def get_queryset(self):
        return News.objects.filter(is_active=True)


# --- ランキング機能を提供するクラス ---
class BadgeRankingMixin:
    def get_badge_ranking_data(self):
        ranking = cache.get("badge_ranking_list")
        if not ranking:
            # キャッシュがなければDBから計算して返す
            ranking = User.objects.annotate(
                badge_count=Count(
                    'userexamstatus',
                    filter=Q(
                        userexamstatus__is_passed=True,
                        userexamstatus__exam__exam_type='main',
                        userexamstatus__exam__is_active=True
                    )
                )
            ).order_by('-badge_count', 'member_num')[:3]

            # キャッシュに保存
            cache.set("badge_ranking_list", ranking, 3600)
        return ranking