from django import forms
from main.models import Question, Choice, Exam
from django.forms import inlineformset_factory, BaseInlineFormSet
import os
from django.conf import settings

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text']

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
    can_delete=False,
    formset=BaseChoiceFormSet
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

    class Meta:
        model = Exam
        fields = ["title", "description", "passing_score", "exams_file", "exam_type", "prerequisite"]

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

    

