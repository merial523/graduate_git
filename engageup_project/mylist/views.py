from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from main.models import Mylist, UserModuleProgress


@login_required
def mylist_index(request):
    """マイリスト一覧画面（進捗率計算付き）"""

    # マイリストデータを取得（関連データも同時取得）
    my_favorites = (
        Mylist.objects.filter(user=request.user)
        .select_related("course", "news")
        .prefetch_related("course__modules")
        .order_by("-created_at")
    )

    # 完了済みモジュールIDのリストを取得
    completed_module_ids = list(
        UserModuleProgress.objects.filter(
            user=request.user, is_completed=True
        ).values_list("module_id", flat=True)
    )

    # 各コースの進捗率を計算
    for item in my_favorites:
        if item.course:
            total_modules = item.course.modules.filter(is_active=True).count()
            if total_modules > 0:
                done_count = UserModuleProgress.objects.filter(
                    user=request.user, module__course=item.course, is_completed=True
                ).count()
                item.course.progress_percent = int((done_count / total_modules) * 100)
            else:
                item.course.progress_percent = 0

    # テンプレートに渡すデータ
    context = {
        "my_favorites": my_favorites,
        "completed_module_ids": completed_module_ids,
        "base_template": "staff/staff_base.html",
    }

    return render(request, "mylist/mylist.html", context)
