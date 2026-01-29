from django.views.generic import TemplateView
from common.views import BaseTemplateMixin

class IndexView(BaseTemplateMixin,TemplateView):

    def get_template_names(self):
        user = self.request.user

        if user.is_authenticated:
            if user.rank == "administer":
                return ["administer/administer_index.html"]
            elif user.rank == "moderator":
                return ["moderator/moderator_index.html"]
            elif user.rank == "staff":
                return ["staff/staff_index.html"]
            elif user.rank == "visitor":
                return ["visitor/visitor_index.html"]

        return ["main/a.html"]

