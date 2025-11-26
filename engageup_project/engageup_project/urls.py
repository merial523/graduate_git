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

urlpatterns = [
    path("admin/", admin.site.urls),
    path("administer/",include("administer.urls")), #トップページはadministerアプリに委譲
    path("", include("main.urls")),  # トップページは common アプリに委譲
    path("enrollments/", include("enrollments.urls")),# トップページは Enrollments アプリに委譲
    path("courses/", include("courses.urls")),  # トップページは Courses アプリに委譲
    path("profile/", include("prof.urls")),# トップページは Profile アプリに委譲
    path("mylist/", include("mylist.urls")),  # トップページは Mylist アプリに委譲
    path('accounts/', include('accounts.urls', namespace='accounts')),  # トップページはaccountsに譲渡
]
