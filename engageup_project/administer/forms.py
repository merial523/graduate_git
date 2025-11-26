# forms.py
from django import forms
from main.models import User

class UserRankForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['rank']  # ラジオボタンにしたいフィールド
        widgets = {
            'rank': forms.RadioSelect()  # ここでラジオボタン指定
        }
