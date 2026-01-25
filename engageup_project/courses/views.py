import json
import random
import os
import google.generativeai as genai
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, ListView, UpdateView, CreateView
from django.urls import reverse_lazy
from django.views.generic.base import ContextMixin

from common.views import BaseCreateView, AdminOrModeratorRequiredMixin, BaseTemplateMixin
from main.models import Course, TrainingModule, TrainingExample, TrainingExampleChoice, User
from .forms import CourseForm, TrainingModuleForm

# =====================================================
# 1. 既存：コース管理 (ListView, CreateView, UpdateView)
# =====================================================

class CoursesIndexView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, TemplateView):
    template_name = "courses/courseIndex.html"

class CourseListView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, ListView):
    model = Course
    template_name = "courses/mo_courses_list.html"
    context_object_name = "courses"
    paginate_by = 10

    def get_queryset(self):
        self.show_deleted = self.request.GET.get("show") == "deleted"
        q = self.request.GET.get("q")
        qs = Course.objects.filter(is_active=not self.show_deleted).order_by("-id")
        if q:
            qs = qs.filter(subject__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # --- 統計データの計算（UserExamStatusを使わない版） ---
        context['total_active_courses'] = Course.objects.filter(is_active=True).count()
        context['total_videos'] = TrainingModule.objects.filter(is_active=True).count()
        
        # 単純に「登録されているユーザーの総数」を表示
        context['total_students'] = User.objects.count() 
        
        context['is_trash_mode'] = self.show_deleted
        context['search_query'] = self.request.GET.get("q", "")
        return context

    def post(self, request, *args, **kwargs):
        # (一括削除・復元の処理はそのまま...)
        action = request.POST.get("action")
        ids = request.POST.getlist("course_ids")
        if ids:
            active_val = (action == "restore")
            Course.objects.filter(id__in=ids).update(is_active=active_val)
            TrainingModule.objects.filter(course_id__in=ids).update(is_active=active_val)
        return redirect(request.get_full_path())
    
class CourseCreateView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, BaseCreateView):
    model = Course
    form_class = CourseForm
    template_name = "courses/mo_courses_form.html"
    success_url = reverse_lazy("courses:courses_list")

    def form_valid(self, form):
        form.instance.is_active = True
        return super().form_valid(form)

class CourseUpdateView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = "courses/mo_courses_form.html"
    success_url = reverse_lazy("courses:courses_list")

    def get_queryset(self):
        return Course.objects.filter(is_active=True)


# =====================================================
# 2. 新規：研修モジュール管理 (管理者用)
# =====================================================

class TrainingModuleCreateView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, ContextMixin, View):
    """コース内に研修を追加"""
    def get(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id)
        # self.get_context_data を使うことで base_template を確実に渡す
        context = self.get_context_data(
            course=course, 
            form=TrainingModuleForm(),
            base_template=self.get_base_template() # 念のための安全策
        )
        return render(request, 'courses/mo_module_form.html', context)

    def post(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id)
        form = TrainingModuleForm(request.POST, request.FILES)
        
        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            
            # --- 教材再利用ロジック ---
            existing = form.cleaned_data.get('existing_file')
            # HTML側の name="training_file" と一致させて取得
            if existing and not request.FILES.get('training_file'):
                module.training_file.name = f"exams_files/{existing}"
            
            module.save()
            return redirect('courses:courses_list')
        
        # フォームが不正な場合も base_template を渡して再表示
        context = self.get_context_data(
            course=course, 
            form=form,
            base_template=self.get_base_template()
        )
        return render(request, 'courses/mo_module_form.html', context)

class TrainingModuleUpdateView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, UpdateView):
    model = TrainingModule
    form_class = TrainingModuleForm
    template_name = "courses/mo_module_form.html" # 研修用のフォームを使う
    
    def get_success_url(self):
        # 編集後はコース一覧に戻る
        return reverse_lazy('courses:courses_list')

    def form_valid(self, form):
        existing = form.cleaned_data.get('existing_file')
        # ★ ここを training_file（モデル名とHTML名）に合わせる
        if existing and not self.request.FILES.get('training_file'):
            form.instance.training_file.name = f"exams_files/{existing}"
        return super().form_valid(form)


# =====================================================
# 3. 新規：AI機能 (要約 ＆ 例題生成)
# =====================================================

class TrainingSummaryAIView(AdminOrModeratorRequiredMixin, View):
    """AIで教材を要約して研修テキストを作成"""
    def post(self, request, module_id):
        module = get_object_or_404(TrainingModule, pk=module_id)
        if not module.training_file:
            return redirect('courses:courses_list') # 本来はエラー画面

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-flash-latest")
        
        with module.training_file.open('rb') as f:
            file_data = f.read()

        prompt = f"この教材から、{module.estimated_time}分で読める研修用テキストを作成してください。重要な点は箇条書きにし、HTMLの<b>タグ等を使って装飾してください。"
        response = model.generate_content([prompt, {'mime_type': 'application/pdf', 'data': file_data}])
        
        module.content_text = response.text
        module.save()
        return redirect('courses:module_edit', pk=module.id)

class TrainingExampleAIView(AdminOrModeratorRequiredMixin, View):
    """AIでテキストから例題を1問生成"""
    def post(self, request, module_id):
        module = get_object_or_404(TrainingModule, pk=module_id)
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-flash-latest")
        
        prompt = f"以下の研修テキストから、理解度を確認する4択の『例題』を1問、JSON形式で作成してください。\n{module.content_text}"
        response = model.generate_content(prompt)
        # (解析と保存ロジック：検定の時と同様の処理を入れる)
        return redirect('courses:module_edit', pk=module.id)


# =====================================================
# 4. 新規：受講者用 (一覧 ＆ 学習画面)
# =====================================================

class StaffCourseListView(BaseTemplateMixin, ListView):
    """受講者向け：アコーディオン形式のコース一覧"""
    model = Course
    template_name = "courses/staff_course_list.html"
    context_object_name = "courses"

    def get_queryset(self):
        # 有効なコースを、中身の研修(modules)と一緒に取得
        return Course.objects.filter(is_active=True).prefetch_related('modules')

class StaffTrainingDetailView(BaseTemplateMixin, ContextMixin, View):
    """受講者向け：研修学習画面 (動画 + テキスト + 例題)"""
    def get(self, request, module_id):
        module = get_object_or_404(TrainingModule, pk=module_id, is_active=True)
        context = self.get_context_data(module=module)
        return render(request, 'courses/staff_training_detail.html', context)