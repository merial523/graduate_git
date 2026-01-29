#メール送信機能実装
#お知らせを通知する


#お知らせの内容を書き込み送信する

#お知らせの内容は入力したものをDBに登録してそれを送信する
#お知らせの一覧画面に
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from common.views import BaseTemplateMixin
from main.models import User,News

from django.views.generic import (
    TemplateView,
    ListView,
    CreateView
)


from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.conf import settings

class NewsCreateView(BaseTemplateMixin,CreateView):
    model = News
    fields = ["title", "content"]
    template_name = "mail/mail_create.html"
    success_url = reverse_lazy("mail:news_history")  # ← URL名にするのが正解

    def form_valid(self, form):
        # ① まず News を保存
        response = super().form_valid(form)

        # ② メール送信用データ取得
        title = form.cleaned_data["title"]
        message = form.cleaned_data["content"]

        users = User.objects.filter(is_active=True).exclude(email="")

        # ③ 全ユーザーに送信
        for user in users:
            send_mail(
                subject=title,
                message=f"[{title}]\n{message}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

        return response


class NewsListView(BaseTemplateMixin,ListView):
    model = News
    template_name = "mail/mail_history.html"
    context_object_name = "news_list"
