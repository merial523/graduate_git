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
from django.http import JsonResponse
from common.views import BaseCreateView, AdminOrModeratorRequiredMixin, BaseTemplateMixin, LoginRequiredCustomMixin
from main.models import Course, TrainingModule, TrainingExample, TrainingExampleChoice, User, UserModuleProgress
from .forms import CourseForm, TrainingModuleForm

# =====================================================
# 1. コース管理 (一覧・作成・編集・削除・復元)
# =====================================================

class CoursesIndexView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, TemplateView):
    template_name = "courses/courseIndex.html"

class CourseListView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, ListView):
    model = Course
    template_name = "courses/mo_courses_list.html"
    context_object_name = "courses"
    paginate_by = 10

    def get_queryset(self):
        # ゴミ箱モードの判定（show=deletedならTrue）
        self.is_trash_mode = self.request.GET.get("show") == "deleted"
        
        # 論理削除(is_deleted)の状態に基づいてフィルタリング
        # ※モデルに is_deleted = models.BooleanField(default=False) が必要です
        queryset = Course.objects.filter(is_deleted=self.is_trash_mode)

        # 1. 検索 (件名)
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(subject__icontains=q)

        # 2. 公開状態フィルタ (ゴミ箱モード以外の場合)
        status = self.request.GET.get("status")
        if not self.is_trash_mode and status:
            if status == "public":
                queryset = queryset.filter(is_active=True)
            elif status == "private":
                queryset = queryset.filter(is_active=False)

        # 3. ソート
        sort = self.request.GET.get("sort", "newest")
        if sort == "newest":
            queryset = queryset.order_by("-id")
        elif sort == "oldest":
            queryset = queryset.order_by("id")
        elif sort == "title":
            queryset = queryset.order_by("subject")
        else:
            queryset = queryset.order_by("-id")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'is_trash_mode': self.is_trash_mode,
            'search_query': self.request.GET.get("q", ""),
            'current_sort': self.request.GET.get("sort", "newest"),
            'current_status': self.request.GET.get("status", "all"),
            # 統計用: 有効かつ公開中のコース数、削除済みコース数
            'total_active_courses': Course.objects.filter(is_deleted=False, is_active=True).count(),
            'total_deleted_courses': Course.objects.filter(is_deleted=True).count(),
        })
        return context

class CourseToggleActiveView(AdminOrModeratorRequiredMixin, View):
    """Ajax用: 個別の公開/非公開切り替え"""
    def post(self, request, pk):
        # 404エラーが出ないよう対象を取得
        course = get_object_or_404(Course, pk=pk)
        
        # 現在の状態を反転させる (True ⇔ False)
        course.is_active = not course.is_active
        course.save()
        
        # 新しい状態をJSONで返す
        return JsonResponse({
            'status': 'success', 
            'is_active': course.is_active
        })

class CourseDeleteView(AdminOrModeratorRequiredMixin, View):
    """個別削除（ゴミ箱へ移動）"""
    def post(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        course.is_deleted = True # 論理削除
        course.save()
        # 紐づく研修もゴミ箱に入れる場合は以下を有効化
        # course.modules.update(is_deleted=True)
        return redirect('courses:courses_list')

class CourseRestoreView(AdminOrModeratorRequiredMixin, View):
    """個別復元（ゴミ箱から戻す）"""
    def post(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        course.is_deleted = False # 復元
        course.save()
        return redirect(reverse_lazy('courses:courses_list') + '?show=deleted')

class CourseBulkActionView(AdminOrModeratorRequiredMixin, View):
    """一括操作（削除・復元・公開・非公開）"""
    def post(self, request):
        ids = request.POST.getlist("course_ids")
        action = request.POST.get("action")
        
        if not ids:
            return redirect('courses:courses_list')

        qs = Course.objects.filter(id__in=ids)
        
        if action == "delete":
            # ゴミ箱へ移動
            qs.update(is_deleted=True)
            # 関連モジュールも削除する場合:
            # TrainingModule.objects.filter(course_id__in=ids).update(is_deleted=True)
            
        elif action == "restore":
            # 復元
            qs.update(is_deleted=False)
            return redirect(reverse_lazy('courses:courses_list') + '?show=deleted')
            
        elif action == "make_public":
            # 一括公開
            qs.update(is_active=True)
            
        elif action == "make_private":
            # 一括非公開
            qs.update(is_active=False)

        return redirect('courses:courses_list')
    
class CourseCreateView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, BaseCreateView):
    model = Course
    form_class = CourseForm
    template_name = "courses/mo_courses_form.html"
    success_url = reverse_lazy("courses:courses_list")
    is_continue_url = "courses:courses_list"
    is_continue = True

    def form_valid(self, form):
        form.instance.is_active = True
        form.instance.is_deleted = False
        return super().form_valid(form)

class CourseUpdateView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = "courses/mo_courses_form.html"
    success_url = reverse_lazy("courses:courses_list")

    def get_queryset(self):
        # ゴミ箱に入っていないものだけ編集可能
        return Course.objects.filter(is_deleted=False)


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
            module.is_active = True # 初期値
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

    def get_queryset(self):
        return TrainingModule.objects.filter(is_active=True)

    def form_valid(self, form):
        existing = form.cleaned_data.get('existing_file')
        if existing and not self.request.FILES.get('training_file'):
            form.instance.training_file.name = f"exams_files/{existing}"
        return super().form_valid(form)
    
class TrainingModuleDeleteView(AdminOrModeratorRequiredMixin, View):
    def post(self, request, module_id):
        module = get_object_or_404(TrainingModule, pk=module_id)
        # 論理削除
        module.is_active = False
        module.save()
        return redirect('courses:courses_list')
    
class TrainingModuleRestoreView(AdminOrModeratorRequiredMixin, View):
    def post(self, request, module_id):
        module = get_object_or_404(TrainingModule, pk=module_id)
        # 復元
        module.is_active = True
        module.save()
        return redirect(reverse_lazy('courses:courses_list') + '?show=deleted')


# =====================================================
# 3. AI自動生成機能 (要約 ＆ 例題)
# =====================================================
# (AI機能部分は変更なし)
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
        # 削除されておらず、かつ公開中のものだけ表示
        return Course.objects.filter(is_deleted=False, is_active=True).prefetch_related('modules')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            # ★ 末尾に list() を付けて、確実に数値のリストにする
            ids = UserModuleProgress.objects.filter(
                user_id=self.request.user.pk, 
                is_completed=True
            ).values_list('module_id', flat=True)
            
            context['completed_module_ids'] = list(ids) # リスト化
        else:
            context['completed_module_ids'] = []
            
        return context
    
class UpdateVideoProgressView(LoginRequiredCustomMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            module_id = data.get('module_id')
            position = data.get('position', 0)
            is_done = data.get('is_done', False)

            # 現在ログインしているユーザーの進捗データを取得または作成
            progress, created = UserModuleProgress.objects.get_or_create(
                user_id=request.user.pk, # ログインユーザーのID
                module_id=module_id
            )
            
            # 再生位置を更新
            progress.last_position = float(position)
            
            # ★ ここがポイント：一度完了(True)になったら、再度見てもFalseに戻らないようにする
            if is_done or progress.is_completed:
                progress.is_completed = True
                
            progress.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
# --- 受講者用：研修詳細 ---
class StaffTrainingDetailView(BaseTemplateMixin, ContextMixin, View):
    """研修学習画面 (動画再生位置の復元に対応)"""
    def get(self, request, module_id):
        # 公開中かつ削除されていないモジュールを取得
        module = get_object_or_404(TrainingModule, pk=module_id, is_active=True)
        
        # このユーザーの再生進捗を取得
        progress = UserModuleProgress.objects.filter(
            user_id=request.user.pk, 
            module=module
        ).first()
        
        context = self.get_context_data(
            module=module,
            # データがなければ 0.0 を渡す（JSでエラーにならないように）
            last_position=progress.last_position if progress else 0.0,
            is_completed=progress.is_completed if progress else False,
            base_template=self.get_base_template()
        )
        return render(request, 'courses/staff_training_detail.html', context)