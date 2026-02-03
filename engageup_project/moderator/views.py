from django.shortcuts import redirect
from django.views.generic import (
    TemplateView,
    FormView,
    ListView,
    UpdateView,
)
from django.urls import reverse, reverse_lazy
from django.db import transaction
from django.utils.crypto import get_random_string
from django.core.exceptions import PermissionDenied

from main.models import User, Badge, Constant, News
from .forms import SequentialUserCreateForm, NewsForm
from accounts.authority import AuthoritySet
from common.views import BaseCreateView, BaseTemplateMixin,AdminOrModeratorRequiredMixin, BadgeRankingMixin

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
# =====================================================from django.views.generic import FormView
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

        FIXED_RANK = "visitor"

        users = []

        for i in range(count):
            number = start_number + i
            username = f"user{number}"
            email = f"{company_code}{number}@{email_address}"

            # 🔒 重複チェック
            if User.objects.filter(username=username).exists():
                form.add_error(None, f"{username} は既に存在します")
                return self.form_invalid(form)

            raw_password = self.generate_password()

            user = User(
                username=username,
                email=email,
                rank=FIXED_RANK   # ← ★ここが正解
            )
            user.set_password(raw_password)

            # メール用に一時保持
            user._raw_password = raw_password
            users.append(user)

        # DB保存
        with transaction.atomic():
            User.objects.bulk_create(users)

        # メール送信
        for user in users:
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



def check_user_duplicate(request):
    start_number = int(request.POST.get("start_number"))
    count = int(request.POST.get("count"))

    company_code = Constant.objects.values_list(
        "company_code", flat=True
    ).first()
    email_address = Constant.objects.values_list(
        "address", flat=True
    ).first()

    duplicates = []

    for i in range(count):
        number = start_number + i
        username = f"user{number}"
        email = f"{company_code}{number}@{email_address}"

        if User.objects.filter(username=username).exists() or \
           User.objects.filter(email=email).exists():
            duplicates.append(username)

    if duplicates:
        return JsonResponse({
            "ok": False,
            "duplicates": duplicates
        })

    return JsonResponse({"ok": True})
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

    def get_success_url(self):
        # URLパラメータから 'from' の値を取得
        origin = self.request.GET.get('from')

        if origin == 'create':
            # 検定新規作成から来た場合：問題管理画面へ
            return reverse('enrollments:question_list', kwargs={'exam_id': self.object.exam.id})
        
        elif origin == 'exam_list':
            # 検定一覧画面から来た場合：検定一覧画面へ戻る
            return reverse('enrollments:exam_list')
        
        # それ以外（バッジ一覧から来た場合など）：バッジ一覧画面へ
        return reverse("moderator:moderatorBadge")




from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
from django.views import View
from common.views import AdminOrModeratorRequiredMixin, BaseTemplateMixin
from main.models import News
from .forms import NewsForm

# =====================================================
# お知らせ管理
# =====================================================

class NewsListView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, ListView):
    model = News
    template_name = "moderator/mo_news_list.html"
    context_object_name = "news_list"
    paginate_by = 10

    def get_queryset(self):
        # ゴミ箱モード判定
        self.is_trash_mode = self.request.GET.get("show") == "deleted"
        
        qs = News.objects.all()

        # 検索
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))

        # フィルタ（公開・非公開）
        status = self.request.GET.get("status")
        if status == "public":
            qs = qs.filter(is_active=True)
        elif status == "private":
            qs = qs.filter(is_active=False)

        # ソート
        sort = self.request.GET.get("sort", "newest")
        if sort == "newest":
            qs = qs.order_by("-created_at")
        elif sort == "oldest":
            qs = qs.order_by("created_at")
        elif sort == "important":
            qs = qs.order_by("-is_important", "-created_at")
            
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'search_query': self.request.GET.get("q", ""),
            'current_sort': self.request.GET.get("sort", "newest"),
            'current_status': self.request.GET.get("status", "all"),
            # 統計用
            'total_count': News.objects.count(),
        })
        return context

class NewsCreateView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, CreateView):
    model = News
    form_class = NewsForm
    template_name = "moderator/mo_news_form.html"
    success_url = reverse_lazy("moderator:news_list")

    def form_valid(self, form):
        form.instance.author = self.request.user # 作成者を記録
        return super().form_valid(form)

class NewsUpdateView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, UpdateView):
    model = News
    form_class = NewsForm
    template_name = "moderator/mo_news_form.html"
    success_url = reverse_lazy("moderator:news_list")

class NewsToggleActiveView(AdminOrModeratorRequiredMixin, View):
    """Ajax用: 公開/非公開切り替え"""
    def post(self, request, pk):
        news = get_object_or_404(News, pk=pk)
        news.is_active = not news.is_active
        news.save()
        return JsonResponse({'status': 'success', 'is_active': news.is_active})

class NewsDeleteView(AdminOrModeratorRequiredMixin, View):
    """削除処理（物理削除または論理削除）"""
    def post(self, request, pk):
        news = get_object_or_404(News, pk=pk)
        news.delete() # または news.is_deleted = True
        return redirect('moderator:news_list')

class NewsBulkActionView(AdminOrModeratorRequiredMixin, View):
    """一括削除"""
    def post(self, request):
        ids = request.POST.getlist("news_ids")
        if ids:
            News.objects.filter(id__in=ids).delete()
        return redirect('moderator:news_list')



