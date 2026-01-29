import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings

# 共通Mixinのインポート
from common.views import AdminOrModeratorRequiredMixin, BaseTemplateMixin
from main.models import User, News

# --- お知らせ作成 ---
class NewsCreateView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, CreateView):
    model = News
    fields = ["title", "content", "category", "is_important"]
    template_name = "mail/mail_create.html" # スクリーンショットに合わせ修正
    success_url = reverse_lazy("mail:news_history")

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)

        # 全アクティブユーザーにメール送信
        title = form.cleaned_data["title"]
        message = form.cleaned_data["content"]
        users = User.objects.filter(is_active=True).exclude(email="")

        for user in users:
            send_mail(
                subject=title,
                message=f"【ねこねこ薬局】{title}\n\n{message}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        return response

# --- お知らせ履歴（一覧） ---
# --- お知らせ履歴（一覧） ---
class NewsListView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, ListView):
    model = News
    template_name = "mail/mail_history.html"
    context_object_name = "news_list"
    paginate_by = 12

    def get_queryset(self):
        # 削除フラグが立っていないお知らせのみを表示
        queryset = News.objects.filter(is_deleted=False)
        
        # 1. 検索
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(content__icontains=query))

        # 2. ジャンルフィルタ
        category = self.request.GET.get('category')
        if category and category != 'all':
            queryset = queryset.filter(category=category)

        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'current_category': self.request.GET.get('category', 'all'),
            'q': self.request.GET.get('q', ''),
        })
        return context

# --- 個別削除（論理削除） ---
class NewsDeleteView(AdminOrModeratorRequiredMixin, View):
    def post(self, request, news_id):
        news = get_object_or_404(News, pk=news_id)
        # 削除フラグを立てて保存（論理削除）
        news.is_deleted = True
        news.save()
        return redirect('mail:news_history')