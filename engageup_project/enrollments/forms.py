# exams/forms.py
from django import forms
from main.models import Question, Choice
from django.forms import inlineformset_factory

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text']

ChoiceFormSet = inlineformset_factory(
    Question, Choice, 
    fields=['text', 'is_correct'],
    extra=4,
    can_delete=False,
)