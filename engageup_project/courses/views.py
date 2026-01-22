from django.views.generic import (
    TemplateView, ListView, UpdateView
)
from django.shortcuts import redirect
from django.urls import reverse_lazy

from common.views import BaseCreateView,AdminOrModeratorRequiredMixin, BaseTemplateMixin

from main.models import Course
from .forms import CourseForm

class CoursesIndexView(
    AdminOrModeratorRequiredMixin,
    BaseTemplateMixin,
    TemplateView
):
    """
    courses アプリのトップページ
    """
    template_name = "courses/courseIndex.html"

class CourseListView(
    AdminOrModeratorRequiredMixin,
    BaseTemplateMixin,
    ListView
):
    model = Course
    template_name = "courses/mo_courses_list.html"
    context_object_name = "courses"
    paginate_by = 10

    def get_queryset(self):
        show = self.request.GET.get("show")

        if show == "deleted":
            return Course.objects.filter(is_active=False).order_by("id")

        return Course.objects.filter(is_active=True).order_by("id")

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        ids = request.POST.getlist("course_ids")

        if ids:
            if action == "delete":
                Course.objects.filter(id__in=ids).update(is_active=False)
            elif action == "restore":
                Course.objects.filter(id__in=ids).update(is_active=True)

        return redirect(request.get_full_path())

class CourseCreateView(
    AdminOrModeratorRequiredMixin,
    BaseTemplateMixin,
    BaseCreateView
):
    model = Course
    form_class = CourseForm
    template_name = "courses/mo_courses_form.html"
    success_url = reverse_lazy("courses:courses_list")

    def form_valid(self, form):
        form.instance.is_active = True
        return super().form_valid(form)

class CourseUpdateView(
    AdminOrModeratorRequiredMixin,
    BaseTemplateMixin,
    UpdateView
):
    model = Course
    form_class = CourseForm
    template_name = "courses/mo_courses_form.html"
    success_url = reverse_lazy("courses:courses_list")

    def get_queryset(self):
        return Course.objects.filter(is_active=True)
