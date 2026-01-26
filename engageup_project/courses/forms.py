import os
from django import forms
from django.conf import settings
from django.forms import inlineformset_factory, BaseInlineFormSet
from main.models import Course, TrainingModule, TrainingExample, TrainingExampleChoice

# 1. コース（科目）作成・編集用
class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["subject", "courseCount", "is_active"]
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: 新人研修 2024'}),
            'courseCount': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# 2. 研修モジュール（動画・テキスト）作成・編集用
class TrainingModuleForm(forms.ModelForm):
    existing_file = forms.ChoiceField(
        choices=[], 
        required=False, 
        label="保存済みライブラリから選ぶ",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = TrainingModule
        fields = ["title", "video", "training_file", "content_text", "estimated_time", "order"]
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'video': forms.FileInput(attrs={'class': 'form-control'}),
            'training_file': forms.FileInput(attrs={'class': 'form-control'}), 
            'content_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'estimated_time': forms.NumberInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 検定(exams_files)フォルダから過去のPDFリストを取得してセット
        library_path = os.path.join(settings.MEDIA_ROOT, 'exams_files')
        file_choices = [('', '--- 新しくアップロードする ---')]
        
        if os.path.exists(library_path):
            files = [f for f in os.listdir(library_path) if f.endswith(('.pdf', '.jpg', '.jpeg', '.png'))]
            for f in files:
                file_choices.append((f, f))
        
        self.fields['existing_file'].choices = file_choices

# 3. 研修内の「例題」作成用
class TrainingExampleForm(forms.ModelForm):
    class Meta:
        model = TrainingExample
        fields = ['text', 'explanation']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '例題文を入力'}),
            'explanation': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': '正解の解説を入力'}),
        }

# 4. 例題の「選択肢」を一括管理するためのセット
ExampleChoiceFormSet = inlineformset_factory(
    TrainingExample, 
    TrainingExampleChoice,
    fields=['text', 'is_correct'],
    extra=4,             # 最初から4つの入力欄を表示
    can_delete=True,     # 削除チェックボックスを表示
    widgets={
        'text': forms.TextInput(attrs={'class': 'form-control'}),
        'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    }
)