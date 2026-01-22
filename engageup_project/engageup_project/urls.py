"""EngageUpProject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings # 追加
from django.conf.urls.static import static # 追加

urlpatterns = [
    path("admin/", admin.site.urls),
    path("administer/",include("administer.urls")), #トップページはadministerアプリに委譲
    path("", include("main.urls")),  # トップページは common アプリに委譲
    path("enrollments/", include("enrollments.urls")),# トップページは Enrollments アプリに委譲
    path("courses/", include("courses.urls")),  # トップページは Courses アプリに委譲
    path("profile/", include("prof.urls")),# トップページは Profile アプリに委譲
    path("mylist/", include("mylist.urls")),  # トップページは Mylist アプリに委譲
    path("moderator/", include("moderator.urls", namespace="moderator")),#トップページはmoderatorアプリに委譲
    path('accounts/', include('accounts.urls', namespace='accounts')),  # トップページはaccountsに譲渡
    path("staff/",include("staff.urls",namespace = "staff")),
]

# 開発環境（DEBUG=True）の場合のみメディアファイルを配信する設定
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
