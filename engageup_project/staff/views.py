from datetime import datetime
from django.shortcuts import redirect, render
from django.views.generic import ListView,TemplateView
from common.views import AdminOrModeratorOrStaffRequiredMixin, BaseTemplateMixin
from main.models import Course, User, UserModuleProgress
from django.db.models import Count, Q

from django.views.generic import TemplateView, ListView
from main.models import News, UserExamStatus
from common.views import BaseTemplateMixin
from moderator.views import BadgeRankingMixin 


class StaffIndexView(BaseTemplateMixin, BadgeRankingMixin, TemplateView):
    template_name = "staff/staff_index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:
            # 1. 🏆 ランキング
            context['badge_ranking'] = self.get_badge_ranking_data()

            # 2. 📊 スタッツ（バッジ数・完了コース）
            context['badges_count'] = UserExamStatus.objects.filter(
                user=user, is_passed=True, exam__exam_type='main', exam__is_active=True
            ).count()

            all_courses = Course.objects.filter(is_active=True).prefetch_related('modules')
            completed_course_count = 0
            for course in all_courses:
                total = course.modules.filter(is_active=True).count()
                if total == 0: continue
                done = UserModuleProgress.objects.filter(user=user, module__course=course, is_completed=True).count()
                if total == done: completed_course_count += 1
            
            context['completed_course_count'] = completed_course_count

            # 3. 📢 お知らせ（最新3件） ★追加
            context['latest_news'] = News.objects.filter(is_active=True).order_by('-created_at')[:3]

            # 4. 📅 挨拶用データ ★追加
            hour = datetime.datetime.now().hour
            if 5 <= hour < 11:
                context['greeting'] = "おはようございます"
            elif 11 <= hour < 18:
                context['greeting'] = "こんにちは"
            else:
                context['greeting'] = "お疲れ様です"

        return context
    
def dashboard_view(request):
    # 本日を基準に月〜日のリストを作成する例
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    
    week_days = []
    labels = ['月', '火', '水', '木', '金', '土', '日']
    
    # ユーザーのログイン履歴（モデル等）から今週分を取得
    # ここでは例として今日だけにチェックを入れる
    for i in range(7):
        target_date = start_of_week + datetime.timedelta(days=i)
        week_days.append({
            'label': labels[i],
            'logged_in': target_date == today # 本来はDBで判定
        })

    return render(request, 'index.html', {
        'week_days': week_days,
        # ...他の変数
    })
    
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
        q = self.request.GET.get("q")  # ★検索キーワード(q)を取得

        # 1. まず「staff」ランクの人だけに絞り込む
        staff_ps = User.objects.filter(rank="staff")

        # 2. 削除済みかどうかのフィルタ
        if show == "deleted":
            staff_ps = staff_ps.filter(is_active=False)
        else:
            staff_ps = staff_ps.filter(is_active=True)

        # 3. ★検索機能の追記
        if q:
            # メールアドレス または 氏名(name) にキーワードが含まれる人を抽出
            staff_ps = staff_ps.filter(
                Q(email__icontains=q) | Q(username__icontains=q)
            )

        return staff_ps.order_by("member_num")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # URLの ?q=... の中身を取得して 'search_query' という名前でHTMLに送る
        context['search_query'] = self.request.GET.get("q", "")
        
        # 削除済みを表示中かどうかのフラグも送っておくとHTMLで便利です
        context['is_trash_mode'] = self.request.GET.get("show") == "deleted"
        
        return context
    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        ids = request.POST.getlist("user_ids")

        if ids:
            if action == "delete":
                User.objects.filter(member_num__in=ids).update(is_active=False)
            elif action == "restore":
                User.objects.filter(member_num__in=ids).update(is_active=True)

        return redirect(request.get_full_path())
    
class StaffNewsListView(BaseTemplateMixin, ListView):
    """受講者用お知らせ一覧画面"""
    model = News
    template_name = "staff/news_list.html"
    context_object_name = "news_list"

    def get_queryset(self):
        # 公開中のお知らせを最新順（作成日時順）に取得
        return News.objects.filter(is_active=True).order_by('-created_at')