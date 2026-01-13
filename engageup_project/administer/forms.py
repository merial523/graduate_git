from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class UserRankForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['rank']
        widgets = {
            'rank': forms.RadioSelect
        }
        labels = {
            'rank': '変更するランク'
        }
