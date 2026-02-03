from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from main.models import Mylist, UserModuleProgress


@login_required
def mylist_index(request):
    """マイリスト一覧画面（進捗率計算付き）"""

    # デバッグ用ログ
    print("=" * 60)
    print("🔍 マイリスト画面のデバッグ開始")
    print(f"👤 ユーザー: {request.user.username} (ID: {request.user.id})")

    # マイリストデータを取得（関連データも同時取得）
    my_favorites = (
        Mylist.objects.filter(user=request.user)
        .select_related("course", "news")
        .prefetch_related("course__modules")  # モジュール情報も取得
        .order_by("-created_at")
    )

    # 完了済みモジュールIDのリストを取得
    completed_module_ids = list(
        UserModuleProgress.objects.filter(
            user=request.user, is_completed=True
        ).values_list("module_id", flat=True)
    )

    # データ件数を確認
    total_count = my_favorites.count()
    print(f"📊 マイリスト総件数: {total_count}")
    print(f"✅ 完了済みモジュール数: {len(completed_module_ids)}")

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

    # 各アイテムの詳細を表示
    if total_count > 0:
        for idx, item in enumerate(my_favorites, 1):
            print(f"\n{'─' * 40}")
            print(f"📌 アイテム {idx}/{total_count}")
            print(f"  ├─ ID: {item.id}")
            print(f"  ├─ 作成日時: {item.created_at}")

            if item.course:
                module_count = item.course.modules.filter(is_active=True).count()
                print(f"  ├─ 種類: 研修コース")
                print(f"  ├─ コース名: {item.course.subject}")
                print(f"  ├─ コースID: {item.course.id}")
                print(f"  ├─ モジュール数: {module_count}")
                print(f"  └─ 進捗率: {item.course.progress_percent}%")
            elif item.news:
                print(f"  ├─ 種類: お知らせ")
                print(f"  ├─ タイトル: {item.news.title}")
                print(f"  └─ お知らせID: {item.news.id}")
            else:
                print(f"  └─ ⚠️ 警告: コースもお知らせも紐づいていません")
    else:
        print("📭 マイリストは空です")

    print("=" * 60)

    # テンプレートに渡すデータ
    context = {
        "my_favorites": my_favorites,
        "completed_module_ids": completed_module_ids,
        "base_template": "staff/staff_base.html",
    }

    return render(request, "mylist/mylist.html", context)
