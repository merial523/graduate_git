import json
import random
import os
import google.generativeai as genai # type: ignore
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, ListView, UpdateView, CreateView
from django.urls import reverse_lazy
from django.views.generic.base import ContextMixin
from django.db.models import Q
from common.views import BaseCreateView, AdminOrModeratorRequiredMixin, BaseTemplateMixin
from main.models import Course, TrainingModule, TrainingExample, TrainingExampleChoice, User
from .forms import CourseForm, TrainingModuleForm

# =====================================================
# 1. コース管理 (一覧・作成・編集)
# =====================================================

class CoursesIndexView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, TemplateView):
    template_name = "courses/courseIndex.html"

class CourseListView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, ListView):
    model = Course
    template_name = "courses/mo_courses_list.html"
    context_object_name = "courses"
    paginate_by = 10

    def get_queryset(self):
        show = self.request.GET.get("show")
        q = self.request.GET.get("q")
        qs = Course.objects.filter(is_active=not (show == "deleted")).order_by("-id")
        if self.request.GET.get("show") == "deleted":
            # 修正：コース自体が削除されているか、中身に1つでも削除された研修があるコースを取得
            qs = Course.objects.filter(Q(is_active=False) | Q(modules__is_active=False)).distinct()
        else:
            qs = Course.objects.filter(is_active=True)

        if q:
            qs = qs.filter(subject__icontains=q)
        return qs.order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'total_active_courses': Course.objects.filter(is_active=True).count(),
            'total_videos': TrainingModule.objects.filter(is_active=True).count(),
            'total_students': User.objects.filter(rank="staff").count(),
            'is_trash_mode': self.request.GET.get("show") == "deleted",
            'search_query': self.request.GET.get("q", "")
        })
        return context

class CourseBulkActionView(AdminOrModeratorRequiredMixin, View):
    """コースの一括削除・復元（NoReverseMatch対策で専用クラス化）"""
    def post(self, request):
        action = request.POST.get("action")
        ids = request.POST.getlist("course_ids")
        if ids:
            active_val = (action == "restore")
            Course.objects.filter(id__in=ids).update(is_active=active_val)
            TrainingModule.objects.filter(course_id__in=ids).update(is_active=active_val)
        
        # 復元時はゴミ箱表示を維持
        if action == "restore":
            return redirect(reverse_lazy('courses:courses_list') + '?show=deleted')
        return redirect('courses:courses_list')
    
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
# 2. 研修モジュール管理 (管理者用)
# =====================================================

class TrainingModuleCreateView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, ContextMixin, View):
    def get(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id)
        context = self.get_context_data(
            course=course, 
            form=TrainingModuleForm(),
            base_template=self.get_base_template()
        )
        return render(request, 'courses/mo_module_form.html', context)

    def post(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id)
        form = TrainingModuleForm(request.POST, request.FILES)
        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            existing = form.cleaned_data.get('existing_file')
            if existing and not request.FILES.get('training_file'):
                module.training_file.name = f"exams_files/{existing}"
            module.save()
            return redirect('courses:courses_list')
        return render(request, 'courses/mo_module_form.html', self.get_context_data(course=course, form=form))

class TrainingModuleUpdateView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, UpdateView):
    model = TrainingModule
    form_class = TrainingModuleForm
    template_name = "courses/mo_module_form.html"
    
    def get_success_url(self):
        return reverse_lazy('courses:courses_list')

    def form_valid(self, form):
        existing = form.cleaned_data.get('existing_file')
        if existing and not self.request.FILES.get('training_file'):
            form.instance.training_file.name = f"exams_files/{existing}"
        return super().form_valid(form)
    
class TrainingModuleDeleteView(AdminOrModeratorRequiredMixin, View):
    def post(self, request, module_id):
        module = get_object_or_404(TrainingModule, pk=module_id)
        module.is_active = False
        module.save()
        return redirect('courses:courses_list')
    
class TrainingModuleRestoreView(AdminOrModeratorRequiredMixin, View):
    def post(self, request, module_id):
        module = get_object_or_404(TrainingModule, pk=module_id)
        module.is_active = True # 復活
        module.save()
        # もし親のコースが非表示なら、一緒に復元させる
        if not module.course.is_active:
            module.course.is_active = True
            module.course.save()
            # メッセージを出すとより親切です（任意）
        return redirect(reverse_lazy('courses:courses_list') + '?show=deleted')


# =====================================================
# 3. AI自動生成機能 (要約 ＆ 例題)
# =====================================================

class TrainingAllAutoGenerateView(AdminOrModeratorRequiredMixin, View):
    def post(self, request, module_id):
        module = get_object_or_404(TrainingModule, pk=module_id)
        if not module.training_file:
            return redirect('courses:module_edit', pk=module.id)

        user_req = request.POST.get('user_instruction', '特になし')
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-flash-latest")

        try:
            with module.training_file.open('rb') as f:
                file_data = f.read()

            prompt = f"""
            資料を読み取り、要約テキストと例題2問を以下のJSON形式で作成してください。
            要望: {user_req}
            
            【出力JSON構造】
            {{
              "summary": "{module.estimated_time}分で学習できる分量のHTML要約",
              "examples": [
                {{
                  "text": "例題の文章",
                  "explanation": "解説",
                  "choices": [
                    {{"text": "選択肢1", "is_correct": true}},
                    {{"text": "選択肢2", "is_correct": false}},
                    {{"text": "選択肢3", "is_correct": false}},
                    {{"text": "選択肢4", "is_correct": false}}
                  ]
                }}
              ]
            }}
            """
            response = model.generate_content([prompt, {'mime_type': 'application/pdf', 'data': file_data}])
            res_text = response.text.replace('```json', '').replace('```', '').strip()
            data = json.loads(res_text)

            module.content_text = data['summary']
            module.save()

            module.examples.all().delete()
            for ex in data['examples']:
                example = TrainingExample.objects.create(
                    module=module, text=ex['text'], explanation=ex['explanation']
                )
                for ch in ex['choices']:
                    TrainingExampleChoice.objects.create(
                        example=example, text=ch['text'], is_correct=ch['is_correct']
                    )
            return redirect('courses:module_edit', pk=module.id)
        except Exception as e:
            return render(request, 'enrollments/enrollments_error.html', {'error': str(e)})


# =====================================================
# 4. 受講者用画面
# =====================================================

class StaffCourseListView(BaseTemplateMixin, ListView):
    model = Course
    template_name = "courses/staff_course_list.html"
    context_object_name = "courses"

    def get_queryset(self):
        return Course.objects.filter(is_active=True).prefetch_related('modules')

class StaffTrainingDetailView(BaseTemplateMixin, ContextMixin, View):
    def get(self, request, module_id):
        module = get_object_or_404(TrainingModule, pk=module_id, is_active=True)
        context = self.get_context_data(
            module=module,
            base_template=self.get_base_template()
        )
        return render(request, 'courses/staff_training_detail.html', context)