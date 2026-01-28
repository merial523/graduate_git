from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView, ListView, UpdateView,CreateView
from main.models import News, UserExamStatus,User
from django.core.cache import cache
from django.db.models import Count, Q

from django.views.generic import TemplateView

from django.core.exceptions import PermissionDenied



class BadgeRankingMixin:
    """バッジ取得数ランキングのデータを提供するMixin"""
    def get_badge_ranking_data(self):
            ranking = cache.get('badge_ranking_list')
            if not ranking:
                ranking = User.objects.filter(rank='staff').annotate(
                    badge_count=Count(
                        'userexamstatus',
                        filter=Q(
                            userexamstatus__is_passed=True,
                            
                            userexamstatus__exam__exam_type='main',
                            userexamstatus__exam__is_active=True
                        )
                    )
                ).order_by('-badge_count')[:3]
                cache.set('badge_ranking_list', ranking, 3600)
            return ranking
        

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
        elif rank == "visitor":
            return reverse_lazy("visitor:visitor_index")


class BaseTemplateMixin:
    """
    ログインユーザーの rank に応じて
    base.html を切り替える Mixin
    """

    def get_base_template(self):
        """
        base.html を決定する専用メソッド
        ★ 絶対に空文字を返さない
        """
        user = self.request.user

        # 未ログイン時
        if not user.is_authenticated:
            return "common/base.html"

        # rank → base.html の対応表
        rank_map = {
            "administer": "administer/administer_base.html",
            "moderator": "moderator/moderator_base.html",
            "staff": "staff/staff_base.html",
            "visitor": "visitor/visitor_base.html",
        }

        # 不正な rank でも common に落とす
        return rank_map.get(user.rank, "common/base.html")

    def get_context_data(self, **kwargs):
        """
        TemplateView が持つ context を壊さずに
        base_template を追加する
        """
        context = super().get_context_data(**kwargs)

        # ★ ここで必ず代入する
        context["base_template"] = self.get_base_template()

        return context

class IndexView(BaseTemplateMixin, BadgeRankingMixin, TemplateView):
    """
    URL「/」にアクセスした際、ランクに合わせて staff_index などを
    そのまま表示し、ランキングデータも渡すView
    """
    def get_template_names(self):
        rank = getattr(self.request.user, 'rank', "")
        if rank == "staff": return ["staff/staff_index.html"]
        elif rank == "administer": return ["administer/administer_index.html"]
        elif rank == "moderator": return ["moderator/moderator_index.html"]
        elif rank == "visitor": return ["visitor/visitor_index.html"]
        else: return ["common/base.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            # ランキングデータをセット
            context['badge_ranking'] = self.get_badge_ranking_data()
            
            # スタッフなら追加の統計もセット
            if self.request.user.rank == "staff":
                context['completed_count'] = UserExamStatus.objects.filter(
                    user=self.request.user, is_passed=True, exam__is_active=True
                ).count()
                context['badges_count'] = UserExamStatus.objects.filter(
                    user=self.request.user, is_passed=True, exam__exam_type='main', exam__is_active=True
                ).count()
                context['latest_news'] = News.objects.filter(is_active=True).order_by('-id')[:3]

                # ---  コース完了のカウントロジックを追加 ---
                from main.models import Course, TrainingModule, UserModuleProgress
                
                # 有効なすべてのコースを取得
                all_courses = Course.objects.filter(is_active=True).prefetch_related('modules')
                completed_course_count = 0

                for course in all_courses:
                    # そのコース内の「有効な研修（動画）」のリスト
                    active_modules = course.modules.filter(is_active=True)
                    
                    # 研修が1つも登録されていないコースは計算から除外
                    if not active_modules.exists():
                        continue
                    
                    # そのユーザーがこのコース内で「完了済み」にした研修の数を数える
                    user_done_count = UserModuleProgress.objects.filter(
                        user = self.request.user,
                        module__course=course,
                        is_completed=True
                    ).count()

                    # 「コース内の全研修数」と「ユーザーの完了数」が一致したら1カウント
                    if active_modules.count() == user_done_count:
                        completed_course_count += 1

                # HTMLで {{ completed_course_count }} として表示可能
                context['completed_course_count'] = completed_course_count

                # --- お知らせ ---
                context['latest_news'] = News.objects.filter(is_active=True).order_by('-id')[:3]
        return context

from django.shortcuts import redirect
from django.urls import reverse_lazy


class LoginRequiredCustomMixin:
    """
    未ログインならログインページへ
    """
    login_url = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(self.login_url)
        return super().dispatch(request, *args, **kwargs)
class AdminOrModeratorOrStaffRequiredMixin(LoginRequiredCustomMixin):
    """
    administer または moderator または staff 以外はログインページへ戻す
    """

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        if user.rank not in ["administer", "moderator","staff"]:
            return redirect(self.login_url)

        return super().dispatch(request, *args, **kwargs)

class AdminOrModeratorRequiredMixin(LoginRequiredCustomMixin):
    """
    administer または moderator 以外はログインページへ戻す
    """

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        if user.rank not in ["administer", "moderator"]:
            return redirect(self.login_url)

        return super().dispatch(request, *args, **kwargs)

class AdminRequiredMixin(LoginRequiredCustomMixin):
    """
    administer 以外はログインページへ戻す
    """

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        if user.rank != "administer":
            return redirect(self.login_url)

        return super().dispatch(request, *args, **kwargs)
