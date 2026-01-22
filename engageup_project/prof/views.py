# prof/views.py
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic.base import ContextMixin
from common.views import BaseTemplateMixin
from main.models import UserExamStatus
from .forms import ProfileForm


class UserProfileView(BaseTemplateMixin, ContextMixin, View):
    """プロフィールの表示"""
    def get(self, request):
        # 合格済みの試験とバッジを取得
        passed_statuses = UserExamStatus.objects.filter(
            user=request.user,
            is_passed=True,
            exam__is_active=True
        ).select_related('exam', 'exam__badge')

        # ContextMixinを使ってbase_templateを確実に渡す
        context = self.get_context_data(
            passed_statuses=passed_statuses,
            base_template=self.get_base_template()
        )
        return render(request, 'prof/user_profile.html', context)

class ProfileUpdateView(BaseTemplateMixin, ContextMixin, View):
    """プロフィールの編集"""
    def get(self, request):
        form = ProfileForm(instance=request.user)
        context = self.get_context_data(form=form, base_template=self.get_base_template())
        return render(request, 'prof/profile_edit.html', context)

    def post(self, request):
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('prof:user_profile') # ★ app_nameに合わせてリダイレクト
        
        context = self.get_context_data(form=form, base_template=self.get_base_template())
        return render(request, 'prof/profile_edit.html', context)