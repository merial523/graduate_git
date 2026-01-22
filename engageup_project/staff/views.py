from django.shortcuts import redirect, render
from django.views.generic import ListView,TemplateView
from common.views import AdminOrModeratorOrStaffRequiredMixin, BaseTemplateMixin
from main.models import User

# Create your views here.

class StaffIndex(TemplateView):
    template_name = "staff/staff_index.html"
class UserListView(
    AdminOrModeratorOrStaffRequiredMixin,
    BaseTemplateMixin,
    ListView
):
    model = User
    template_name = "staff/st_user_list.html"
    context_object_name = "users"
    paginate_by = 10

    def get_queryset(self):
        show = self.request.GET.get("show")

        if show == "deleted":
            return User.objects.filter(is_active=False).order_by("member_num")

        return User.objects.filter(is_active=True).order_by("member_num")

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        ids = request.POST.getlist("user_ids")

        if ids:
            if action == "delete":
                User.objects.filter(id__in=ids).update(is_active=False)
            elif action == "restore":
                User.objects.filter(id__in=ids).update(is_active=True)

        return redirect(request.get_full_path())
