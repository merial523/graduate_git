# common/middleware.py
from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse


class LoginRequiredMiddleware:
    """
    未ログインのユーザーをログインページにリダイレクトするミドルウェア
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 除外したいURLリスト
        exempt_urls = [
            reverse('accounts:login'),          # ログインページ
            reverse('admin:index'),    # 管理画面
        ]

        # もしログインしていれば通す
        if request.user.is_authenticated:
            return self.get_response(request)

        # 除外URLまたは静的ファイルなら通す
        if request.path in exempt_urls or request.path.startswith(settings.STATIC_URL):
            return self.get_response(request)

        # それ以外 → ログインページへリダイレクト
        return redirect(settings.LOGIN_URL)
