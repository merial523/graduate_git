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
            "administer", "administer_index",
            "moderator", "moderator_index",
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
            user._raw_password = raw_password
            users.append(user)

        with transaction.atomic():
            User.objects.bulk_create(users)

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
        if q:
            return Badge.objects.filter(name__icontains=q)
        return Badge.objects.all()
    
    def get_queryset(self):
        return Badge.objects.filter(is_active=True)


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
class NewsListView(
    AdminOrModeratorRequiredMixin,
    BaseTemplateMixin,
    ListView
):
    model = News
    template_name = "moderator/mo_news_list.html"
    context_object_name = "news_"
    paginate_by = 10

    def get_queryset(self):
        show = self.request.GET.get("show")
        qs = News.objects.order_by("id")

        if show == "deleted":
            return qs.filter(is_active=False)

        return qs.filter(is_active=True)

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        ids = request.POST.getlist("news_ids")

        if ids:
            qs = News.objects.filter(id__in=ids)
            if action == "delete":
                qs.update(is_active=False)
            elif action == "restore":
                qs.update(is_active=True)

        return redirect(request.get_full_path())


class NewsCreateView(
    AdminOrModeratorRequiredMixin,
    BaseTemplateMixin,
    BaseCreateView
):
    model = News
    form_class = NewsForm
    template_name = "moderator/mo_news_form.html"
    success_url = reverse_lazy("moderator:news_list")

    def form_valid(self, form):
        form.instance.is_active = True
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
    """バッジ取得数ランキングのデータを提供するMixin"""
    
    def get_badge_ranking_data(self):
        # 1. キャッシュを確認
        ranking = cache.get('badge_ranking_list')

        if not ranking:
            # 2. キャッシュが空なら集計（上位3名）
            ranking = User.objects.annotate(
                badge_count=Count(
                    'userexamstatus',
                    filter=Q(
                        userexamstatus__is_passed=True,
                        userexamstatus__exam__exam_type='main',
                        userexamstatus__exam__is_active=True
                    )
                )
            ).order_by('-badge_count')[:3]

            # 3. 1時間(3600秒)キャッシュ
            cache.set('badge_ranking_list', ranking, 3600)

        return ranking
