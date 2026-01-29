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
        fields = ["title", "content","is_active", 'is_important']


from main.models import Badge # Badgeモデルの名前はプロジェクトに合わせて調整してください

class BadgeForm(forms.ModelForm):
    name = forms.CharField(
        label="バッジ名称",
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'required': 'required',
            'placeholder': 'バッジ名を入力してください'
        })
    )
    # アイコンは画像がない場合もあるため required=False にしていますが、必須なら True にしてください
    icon = forms.ImageField(
        label="アイコン画像",
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Badge
        fields = ['name', 'icon']
