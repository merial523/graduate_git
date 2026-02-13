from django.views.generic import ListView
from django.db.models import Prefetch
from main.models import Mylist, UserModuleProgress, TrainingModule # 必要に応じてインポート追加
from common.views import LoginRequiredCustomMixin, BaseTemplateMixin

class MylistIndexView(LoginRequiredCustomMixin, BaseTemplateMixin, ListView):
    """マイリスト一覧画面（進捗率計算・非表示除外対応）"""
    
    model = Mylist
    template_name = "mylist/mylist.html"
    context_object_name = "my_favorites"

    def get_queryset(self):
        # 1. 有効な（非表示でない）研修だけを取得する条件
        active_modules_qs = TrainingModule.objects.filter(is_active=True)
        
        # 2. マイリストを取得し、有効な研修だけを事前に読み込む（Prefetch）
        return (
            Mylist.objects.filter(user=self.request.user)
            .select_related("course", "news")
            .prefetch_related(
                Prefetch("course__modules", queryset=active_modules_qs)
            )
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # 完了済みモジュールIDの取得
        context["completed_module_ids"] = list(
            UserModuleProgress.objects.filter(
                user=user, is_completed=True
            ).values_list("module_id", flat=True)
        )

        # 各コースの進捗率を計算
        # get_queryset で prefetch されているため、item.course.modules.all() は有効なもののみ
        for item in context["my_favorites"]:
            if item.course:
                active_modules = list(item.course.modules.all()) # すでに絞り込み済み
                total_modules = len(active_modules)

                if total_modules > 0:
                    done_count = UserModuleProgress.objects.filter(
                        user=user, 
                        module__in=active_modules, 
                        is_completed=True
                    ).count()
                    item.course.progress_percent = int((done_count / total_modules) * 100)
                else:
                    item.course.progress_percent = 0
        
        return context