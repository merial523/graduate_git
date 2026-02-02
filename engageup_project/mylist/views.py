import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views import View
from django.db.models import Prefetch
from main.models import News, Course, Mylist, UserModuleProgress

@login_required
def mylist_index(request):
    # ログイン中のユーザーに紐づくマイリストデータを全て取得
    # .select_related('course') を入れることで表示が速くなります
    mylist_items = Mylist.objects.filter(user=request.user).select_related('course', 'news').order_by('-id')

    context = {
        'mylist_items': mylist_items,
        'base_template': "staff/staff_base.html",
    }
    return render(request, "mylist/mylist.html", context)

# --- お知らせ用のお気に入り操作 ---

@login_required
def add_favorite_news(request, news_id):
    """お知らせをマイリストに追加"""
    news = get_object_or_404(News, id=news_id)
    Mylist.objects.get_or_create(user=request.user, news=news)
    # 元のお知らせ詳細画面へ戻る
    return redirect("staff:news_list") # 適切なリダイレクト先に変更してください

@login_required
def remove_favorite_news(request, news_id):
    """お知らせをマイリストから削除"""
    Mylist.objects.filter(user=request.user, news_id=news_id).delete()
    return redirect("staff:news_list")

# --- 研修コース用のお気に入り操作（Ajax推奨） ---

# mylist/views.py
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from main.models import Course, Mylist

@login_required
def toggle_course_favorite(request, course_id):
    """コースのお気に入り登録・解除を行うAjaxビュー"""
    if request.method == "POST":
        course = get_object_or_404(Course, id=course_id)
        
        # 自分のマイリストにこのコースが既にあるか探す
        favorite = Mylist.objects.filter(user=request.user, course=course)
        
        if favorite.exists():
            favorite.delete()
            return JsonResponse({"status": "success", "action": "removed"})
        else:
            Mylist.objects.create(user=request.user, course=course)
            return JsonResponse({"status": "success", "action": "added"})
            
    return JsonResponse({"status": "error"}, status=400)