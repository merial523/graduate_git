import json
import random
import os
import google.generativeai as genai
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, ListView, UpdateView, CreateView
from django.urls import reverse_lazy, reverse
from django.views.generic.base import ContextMixin
from django.db.models import Q, Prefetch
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction  # トランザクション管理

from common.views import (
    BaseCreateView,
    AdminOrModeratorRequiredMixin,
    BaseTemplateMixin,
    LoginRequiredCustomMixin,
)
from main.models import (
    Course,
    TrainingModule,
    TrainingExample,
    TrainingExampleChoice,
    UserModuleProgress,
    Mylist,
    News,
)
from .forms import CourseForm, TrainingModuleForm

# =====================================================
# 1. コース管理 (管理者用)
# =====================================================


class CoursesIndexView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, TemplateView):
    template_name = "courses/courseIndex.html"


class CourseListView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, ListView):
    model = Course
    template_name = "courses/mo_courses_list.html"
    context_object_name = "courses"
    paginate_by = 10

    def get_queryset(self):
        self.is_trash_mode = self.request.GET.get("show") == "deleted"
        queryset = Course.objects.filter(is_deleted=self.is_trash_mode)
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(subject__icontains=q)
        status = self.request.GET.get("status")
        if not self.is_trash_mode and status:
            if status == "public":
                queryset = queryset.filter(is_active=True)
            elif status == "private":
                queryset = queryset.filter(is_active=False)
        sort = self.request.GET.get("sort", "newest")
        if sort == "oldest":
            queryset = queryset.order_by("id")
        elif sort == "title":
            queryset = queryset.order_by("subject")
        else:
            queryset = queryset.order_by("-id")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "is_trash_mode": self.is_trash_mode,
                "search_query": self.request.GET.get("q", ""),
                "current_sort": self.request.GET.get("sort", "newest"),
                "current_status": self.request.GET.get("status", "all"),
                "total_active_courses": Course.objects.filter(
                    is_deleted=False, is_active=True
                ).count(),
                "total_deleted_courses": Course.objects.filter(is_deleted=True).count(),
            }
        )
        return context


class CourseToggleActiveView(AdminOrModeratorRequiredMixin, View):
    def post(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        course.is_active = not course.is_active
        course.save()
        return JsonResponse({"status": "success", "is_active": course.is_active})


class CourseBulkActionView(AdminOrModeratorRequiredMixin, View):
    def post(self, request):
        ids = request.POST.getlist("course_ids")
        action = request.POST.get("action")
        if not ids:
            return redirect("courses:courses_list")
        qs = Course.objects.filter(id__in=ids)
        if action == "delete":
            qs.update(is_deleted=True)
        elif action == "restore":
            qs.update(is_deleted=False)
            return redirect(reverse_lazy("courses:courses_list") + "?show=deleted")
        elif action == "make_public":
            qs.update(is_active=True)
        elif action == "make_private":
            qs.update(is_active=False)
        return redirect("courses:courses_list")


class CourseCreateView(
    AdminOrModeratorRequiredMixin, BaseTemplateMixin, BaseCreateView
):
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
        return Course.objects.filter(is_deleted=False)


# =====================================================
# 2. 研修モジュール管理 (管理者用)
# =====================================================


class TrainingModuleCreateView(
    AdminOrModeratorRequiredMixin, BaseTemplateMixin, ContextMixin, View
):
    def get(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id)
        context = self.get_context_data(
            course=course,
            form=TrainingModuleForm(),
            base_template=self.get_base_template(),
        )
        return render(request, "courses/mo_module_form.html", context)

    def post(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id)
        form = TrainingModuleForm(request.POST, request.FILES)
        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            module.is_active = True
            existing = form.cleaned_data.get("existing_file")
            if existing and not request.FILES.get("training_file"):
                module.training_file.name = f"exams_files/{existing}"
            module.save()
            if request.POST.get("after_save") == "ai":
                return redirect(
                    reverse("courses:module_edit", args=[module.pk]) + "#ai"
                )
            return redirect("courses:courses_list")
        return render(
            request,
            "courses/mo_module_form.html",
            self.get_context_data(course=course, form=form),
        )


class TrainingModuleUpdateView(
    AdminOrModeratorRequiredMixin, BaseTemplateMixin, UpdateView
):
    model = TrainingModule
    form_class = TrainingModuleForm
    template_name = "courses/mo_module_form.html"
    success_url = reverse_lazy("courses:courses_list")

    def get_queryset(self):
        return TrainingModule.objects.filter(is_active=True)

    def form_valid(self, form):
        existing = form.cleaned_data.get("existing_file")
        if existing and not self.request.FILES.get("training_file"):
            form.instance.training_file.name = f"exams_files/{existing}"
        return super().form_valid(form)


class TrainingModuleDeleteView(AdminOrModeratorRequiredMixin, View):
    def post(self, request, module_id):
        module = get_object_or_404(TrainingModule, pk=module_id)
        module.is_active = False
        module.save()
        return redirect("courses:courses_list")


class TrainingModuleRestoreView(AdminOrModeratorRequiredMixin, View):
    def post(self, request, module_id):
        module = get_object_or_404(TrainingModule, pk=module_id)
        module.is_active = True
        module.save()
        return redirect(reverse_lazy("courses:courses_list") + "?show=deleted")


# =====================================================
# 3. AI自動生成機能
# =====================================================
class TrainingAllAutoGenerateView(AdminOrModeratorRequiredMixin, View):
    def post(self, request, module_id):
        module = get_object_or_404(TrainingModule, pk=module_id)
        if not module.training_file:
            return redirect("courses:module_edit", pk=module.id)
        user_req = request.POST.get("user_instruction", "特になし")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-flash-latest")
        try:
            with module.training_file.open("rb") as f:
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
            response = model.generate_content(
                [prompt, {"mime_type": "application/pdf", "data": file_data}]
            )
            res_text = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(res_text)
            module.content_text = data["summary"]
            module.save()
            module.examples.all().delete()
            for ex in data["examples"]:
                example = TrainingExample.objects.create(
                    module=module, text=ex["text"], explanation=ex["explanation"]
                )
                for ch in ex["choices"]:
                    TrainingExampleChoice.objects.create(
                        example=example, text=ch["text"], is_correct=ch["is_correct"]
                    )
            return redirect("courses:module_edit", pk=module.id)
        except Exception as e:
            return render(
                request, "enrollments/enrollments_error.html", {"error": str(e)}
            )


# =====================================================
# 4. 受講者用画面 (一覧・詳細・進捗)
# =====================================================


class StaffCourseListView(BaseTemplateMixin, ListView):
    """研修コース一覧（受講者用）"""

    model = Course
    template_name = "courses/staff_course_list.html"
    context_object_name = "courses"

    def get_queryset(self):
        return Course.objects.filter(is_deleted=False, is_active=True).prefetch_related(
            "modules"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["categories"] = (
            Course.objects.filter(is_active=True, is_deleted=False)
            .values_list("subject", flat=True)
            .distinct()
        )

        if user.is_authenticated:
            # 完了済みモジュール
            context["completed_module_ids"] = list(
                UserModuleProgress.objects.filter(
                    user=user, is_completed=True
                ).values_list("module_id", flat=True)
            )
            # ★重要: マイリスト登録済みのコースIDを取得
            my_fav_course_ids = set(
                Mylist.objects.filter(user=user, course__isnull=False).values_list(
                    "course_id", flat=True
                )
            )

            # 各コースに「is_mylist」フラグを立てる
            for course in context["courses"]:
                course.is_mylist = course.id in my_fav_course_ids

                # 進捗計算
                total_modules = course.modules.filter(is_active=True).count()
                if total_modules > 0:
                    done_count = UserModuleProgress.objects.filter(
                        user=user, module__course=course, is_completed=True
                    ).count()
                    course.progress_percent = int((done_count / total_modules) * 100)
                else:
                    course.progress_percent = 0
        return context


class StaffTrainingDetailView(BaseTemplateMixin, ContextMixin, View):
    def get(self, request, module_id):
        module = get_object_or_404(TrainingModule, pk=module_id, is_active=True)
        all_modules = list(module.course.modules.filter(is_active=True).order_by("id"))
        try:
            current_idx = all_modules.index(module)
            prev_module = all_modules[current_idx - 1] if current_idx > 0 else None
            next_module = (
                all_modules[current_idx + 1]
                if current_idx < len(all_modules) - 1
                else None
            )
        except ValueError:
            prev_module = next_module = None
        progress = UserModuleProgress.objects.filter(
            user_id=request.user.pk, module=module
        ).first()
        context = self.get_context_data(
            module=module,
            last_position=progress.last_position if progress else 0.0,
            is_completed=progress.is_completed if progress else False,
            prev_module=prev_module,
            next_module=next_module,
            base_template=self.get_base_template(),
        )
        return render(request, "courses/staff_training_detail.html", context)


class UpdateVideoProgressView(LoginRequiredCustomMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            module_id = data.get("module_id")
            position = data.get("position", 0)
            is_done = data.get("is_done", False)
            progress, created = UserModuleProgress.objects.get_or_create(
                user_id=request.user.pk, module_id=module_id
            )
            progress.last_position = float(position)
            if is_done or progress.is_completed:
                progress.is_completed = True
            progress.save()
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)


# =====================================================
# 5. マイリスト関連ビュー
# =====================================================


@login_required
def mylist_index(request):
    """マイリスト一覧画面"""
    my_favorites = (
        Mylist.objects.filter(user=request.user)
        .select_related("course", "news")
        .order_by("-created_at")
    )
    context = {"my_favorites": my_favorites, "base_template": "staff/staff_base.html"}
    return render(request, "mylist/mylist.html", context)


@login_required
@transaction.atomic
def toggle_course_favorite(request, course_id):
    """【講座】ハートを押した時のAjax処理"""
    if request.method == "POST":
        try:
            course = get_object_or_404(Course, id=course_id)
            favorite = Mylist.objects.filter(user=request.user, course=course).first()
            if favorite:
                favorite.delete()
                return JsonResponse({"status": "success", "action": "removed"})

            Mylist.objects.create(user=request.user, course=course)
            return JsonResponse({"status": "success", "action": "added"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)


@login_required
@transaction.atomic
def toggle_news_favorite(request, news_id):
    """【お知らせ】ハートを押した時のAjax処理"""
    if request.method == "POST":
        try:
            news = get_object_or_404(News, id=news_id)
            favorite = Mylist.objects.filter(user=request.user, news=news).first()
            if favorite:
                favorite.delete()
                return JsonResponse({"status": "success", "action": "removed"})
            Mylist.objects.create(user=request.user, news=news)
            return JsonResponse({"status": "success", "action": "added"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)
