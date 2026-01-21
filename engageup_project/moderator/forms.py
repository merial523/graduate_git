from django import forms
from main.models import News, User

class SequentialUserCreateForm(forms.Form):


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

class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ["title", "content","is_active"]
