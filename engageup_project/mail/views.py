from django.core.mail import EmailMessage
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.template.loader import render_to_string

User = get_user_model()

def send_selected_mail(request):
    if request.method == "POST":
        user_ids = request.POST.getlist("user_ids")

        users = User.objects.filter(
            id__in=user_ids,
            is_active=True
        )

        for user in users:
            # メール本文（テンプレート）
            body = render_to_string(
                "mail/user_notice.txt",
                {"user": user}
            )

            email = EmailMessage(
                subject="【重要】お知らせ",
                body=body,
                to=[user.email],  # ← メアドに送信
            )
            email.send()

        return redirect("staff:staff_index")
