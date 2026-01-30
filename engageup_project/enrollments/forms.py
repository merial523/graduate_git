from django import forms
from main.models import Question, Choice, Exam
from django.forms import inlineformset_factory, BaseInlineFormSet
import os
from django.conf import settings

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text']
        #タイトルにrequired属性を追加
        widgets = {
            # TextInput ではなく Textarea を使うのが正解です
            'text': forms.Textarea(attrs={
                'required': 'required',
                'class': 'form-control',
                'rows': 4,  # 行数で高さを指定
                'placeholder': 'ここに質問文を入力してください',
                'autofocus': 'autofocus',
            }),
        }

class BaseChoiceFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        correct_count = 0

        for form in self.forms:
            # 削除予定のフォームは無視
            if self.can_delete and self._should_delete_form(form):
                continue

            # 空フォームは無視
            if not form.cleaned_data:
                continue

            if form.cleaned_data.get('is_correct'):
                correct_count += 1

        if correct_count == 0:
            raise forms.ValidationError(
                "正解の選択肢を1つ以上選んでください。"
            )

ChoiceFormSet = inlineformset_factory(
    Question, Choice, 
    fields=['text', 'is_correct'],
    extra=4,
    can_delete=True,
    formset=BaseChoiceFormSet,
    widgets={
        'text': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
        'is_correct': forms.CheckboxInput(attrs={'class': 'is-correct-check'}), # requiredを外す
    }
)
# 編集用（既存の選択肢のみ表示）
EditChoiceFormSet = inlineformset_factory(
    Question,
    Choice,
    fields=['text', 'is_correct'],
    extra=0,
    can_delete=True,
    formset=BaseChoiceFormSet
)

class ExamForm(forms.ModelForm):
    exam_file = forms.ChoiceField(
        choices=[],
        required=False,
        label="保存済みから選ぶ")
    
    #タイトルにrequired属性を追加
    title = forms.CharField(
        label="試験タイトル",
        widget=forms.TextInput(attrs={'required': 'required'})
    )
    #合格基準点にrequired属性を追加
    passing_score = forms.IntegerField(
        label="合格基準点",
        widget=forms.NumberInput(attrs={'required': 'required'})
    )

    class Meta:
        model = Exam
        fields = ["title", "description", "passing_score", 'time_limit', "exams_file", "exam_type", "prerequisite"]
        #テキストをpdfのみに制限をかける
        widgets = {
            'exams_file': forms.ClearableFileInput(attrs={'accept': '.pdf'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 保存済みファイルのリストを取得
        files_dir = os.path.join(settings.MEDIA_ROOT, 'exams_files')
        if os.path.exists(files_dir):
            files = os.listdir(files_dir)
        else:
            files = []

        file_choices = [('', '--- 選択してください ---')] + [(f, f) for f in files]
        self.fields['exam_file'].choices = file_choices

        # デザインをねこねこ薬局風にするための設定
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': '例：2024年度 新人研修テスト'}),
            'passing_score': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            
            # ★ 制限時間のウィジェット設定
            'time_limit': forms.NumberInput(attrs={
                'min': 0, 
                'placeholder': '30',
                'class': 'form-control' # CSS側でスタイルを当てやすくするため
            }),
            
            'description': forms.Textarea(attrs={'rows': 5}),
            'exam_type': forms.Select(),
        }

    

