from django.shortcuts import redirect, render
from django.views.generic import ListView,TemplateView
from common.views import AdminOrModeratorOrStaffRequiredMixin, BaseTemplateMixin
from main.models import User

from django.views.generic import TemplateView, ListView
from main.models import News, UserExamStatus
from common.views import BaseTemplateMixin
from moderator.views import BadgeRankingMixin 


class StaffIndex(TemplateView):
    template_name = "staff/staff_index.html"
class UserListView(
    AdminOrModeratorOrStaffRequiredMixin,
    BaseTemplateMixin,
    ListView
):
    model = User
    template_name = "staff/st_user_list.html"
    context_object_name = "users"
    paginate_by = 10

    def get_queryset(self):
        show = self.request.GET.get("show")

        if show == "deleted":
            return User.objects.filter(is_active=False).order_by("member_num")

        return User.objects.filter(is_active=True).order_by("member_num")

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        ids = request.POST.getlist("user_ids")

        if ids:
            if action == "delete":
                User.objects.filter(id__in=ids).update(is_active=False)
            elif action == "restore":
                User.objects.filter(id__in=ids).update(is_active=True)

        return redirect(request.get_full_path())
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:
            # 1. 🏆 ランキングデータを取得 (Mixinの機能を使用)
            context['badge_ranking'] = self.get_badge_ranking_data()
            
            # 2. 🔔 最新のニュース（プレビュー用：3件）
            context['latest_news'] = News.objects.filter(is_active=True).order_by('-id')[:3]

            # 3. 📊 自分の学習統計（本物の数字を計算）
            # 合格した検定の総数
            context['completed_count'] = UserExamStatus.objects.filter(
                user=user, is_passed=True, exam__is_active=True
            ).count()
            # 獲得したバッジの総数（本試験のみ）
            context['badges_count'] = UserExamStatus.objects.filter(
                user=user, is_passed=True, exam__exam_type='main', exam__is_active=True
            ).count()

        return context

class StaffNewsListView(BaseTemplateMixin, ListView):
    """受講者用お知らせ一覧画面"""
    model = News
    template_name = "staff/news_list.html"
    context_object_name = "news_list"

    def get_queryset(self):
        return News.objects.filter(is_active=True).order_by('-id')
