from django import forms
from main.models import User

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['avatar', 'remarks']
        widgets = {
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }