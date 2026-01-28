from django.shortcuts import redirect, render
from django.views.generic import ListView,TemplateView
from common.views import AdminOrModeratorOrStaffRequiredMixin, BaseTemplateMixin
from main.models import Course, User, UserModuleProgress
from django.db.models import Count, Q

from django.views.generic import TemplateView, ListView
from main.models import News, UserExamStatus
from common.views import BaseTemplateMixin
from moderator.views import BadgeRankingMixin 


class StaffIndexView(BaseTemplateMixin, 
                        BadgeRankingMixin, 
                        TemplateView):
    template_name = "staff/staff_index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:
            # 1. 🏆 ランキングデータを取得
            context['badge_ranking'] = self.get_badge_ranking_data()

            # 獲得したバッジの総数
            context['badges_count'] = UserExamStatus.objects.filter(
                user=user, is_passed=True, exam__exam_type='main', exam__is_active=True
            ).count()

            # --- ★ 新規：完了した「コース」のカウントロジック ---
            # 有効な全コースを取得
            all_courses = Course.objects.filter(is_active=True).prefetch_related('modules')
            completed_course_count = 0

            for course in all_courses:
                # A. そのコース内にある「有効な研修（動画）」の総数
                total_modules_count = course.modules.filter(is_active=True).count()
                
                # 研修が1つも登録されていないコースはスキップ
                if total_modules_count == 0:
                    continue

                # B. そのコース内の研修で、ユーザーが「完了(is_completed=True)」させた数
                user_completed_modules_count = UserModuleProgress.objects.filter(
                    user=user,
                    module__course=course,
                    is_completed=True
                ).count()

                # C. 「全研修数」と「完了数」が一致したら、そのコースは完了！
                if total_modules_count == user_completed_modules_count:
                    completed_course_count += 1

            # HTMLで {{ completed_course_count }} として使えるように送る
            context['completed_course_count'] = completed_course_count

        return context
    
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
        return News.objects.filter(is_active=True).order_by('-id')
