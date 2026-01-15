from django.shortcuts import render, redirect
from django.views.generic import ListView
from main.models import Course
# from .forms import CourseForm


# ------------------------------
# Courses
# ------------------------------

def courses_index(request):
    return render(request, "Courses/4101.html")


def courses_text_upload(request):
    return render(request, "Courses/mo_text_upload.html")



class CourseListView(ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 10

    def get_queryset(self):
        """講座一覧表示（論理削除切り替え）"""
        show = self.request.GET.get('show')

        if show == 'all':           # 全講座表示
            return Course.objects.all()
        else:                       # 有効な講座のみ表示
            return Course.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        """全表示フラグをテンプレートへ"""
        context = super().get_context_data(**kwargs)
        context['show_all'] = self.request.GET.get('show') == 'all'
        return context

    def post(self, request, *args, **kwargs):
        """選択された講座を論理削除"""
        action = request.POST.get('action')
        course_ids = request.POST.getlist('course_ids')

        if action == 'deactivate' and course_ids:
            Course.objects.filter(
                id__in=course_ids,
                is_active=True
            ).update(is_active=False)

        return redirect(request.path)
