from django import forms
from main.models import User

class UserUpdateForm(forms.ModelForm):
    password = forms.CharField(
        label="パスワード",
        widget=forms.PasswordInput,
        required=True
    )
    password_check = forms.CharField(
        label="パスワード確認用",
        widget=forms.PasswordInput,
        required=True,
    )

    class Meta:
        model = User
        fields = ["username"]  # passwordは保存しない

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_check = cleaned_data.get("password_check")

        if password and password_check and password != password_check:
            raise forms.ValidationError("パスワードが一致しません")

        return cleaned_data
