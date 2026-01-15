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

class AdSequentialUserCreateForm(forms.Form):

    company_code = forms.CharField(
        label="会社コード（例: oom）",
        max_length=20,
        required=True
    )

    start_number = forms.IntegerField(
        label="開始番号",
        min_value=1
    )

    count = forms.IntegerField(
        label="作成人数",
        min_value=1,
        max_value=100
    )

    rank = forms.ChoiceField(
        label="ランク",
        choices=User.RANK_CHOICES,
        initial="visitor",
        widget=forms.RadioSelect
    )
    address = forms.CharField(
        label="メールアドレス@の先",
        max_length=20,
        required=True
    )

from main.models import Constant

class ConstantForm(forms.ModelForm):
    class Meta:
        model = Constant
        fields = ['company_code', 'address']