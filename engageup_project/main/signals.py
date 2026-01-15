from .models import Constant

def create_initial_constant(sender, **kwargs):
    if not Constant.objects.exists():
        Constant.objects.create(
            company_code='exa',
            address='gmail.com'
        )