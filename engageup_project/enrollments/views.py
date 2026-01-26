import json
import random
import os
import fitz  # type: ignore
import google.generativeai as genai  # type: ignore
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic.base import ContextMixin 
from django.views.generic import ListView, UpdateView, TemplateView
from django.urls import reverse_lazy
from django.http import JsonResponse
from google.generativeai.types import HarmCategory, HarmBlockThreshold  # type: ignore
from common.views import BaseCreateView, BaseTemplateMixin, AdminOrModeratorRequiredMixin
from main.models import Exam, Question, Badge, Choice, UserExamStatus
from .forms import QuestionForm, ChoiceFormSet, EditChoiceFormSet, ExamForm

# --- 基本表示 ---

class EnrollmentsHistoryView(BaseTemplateMixin, TemplateView):
    template_name = "enrollments/enrollments_history.html"


# --- 検定管理（管理者・モデレーター用） ---

class ExamListView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, ListView):
    model = Exam
    template_name = "enrollments/all_enrollments.html"
    context_object_name = "exams"
    paginate_by = 20

    def get_queryset(self):
        self.is_trash_mode = self.request.GET.get("show") == "deleted"
        queryset = Exam.objects.filter(is_deleted=self.is_trash_mode)
        
        # 1. 検索 (q)
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(title__icontains=query)

        # 2. 試験種別フィルタ (type)
        exam_type = self.request.GET.get('type')
        if exam_type in ['main', 'mock']:
            queryset = queryset.filter(exam_type=exam_type)

        # 3. 並べ替え (sort)
        sort = self.request.GET.get('sort', 'newest')
        sort_dict = {
            'newest': '-created_at',
            'oldest': 'created_at',
            'title': 'title'
        }
        return queryset.order_by(sort_dict.get(sort, '-created_at'))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_trash_mode'] = self.is_trash_mode
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        context['current_type'] = self.request.GET.get('type', 'all')
        context['q'] = self.request.GET.get('q', '')
        return context

class ExamCreateView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, BaseCreateView):
    model = Exam
    template_name = "enrollments/exam_create.html"
    success_url = reverse_lazy("enrollments:exam_list") 
    form_class = ExamForm
    is_continue_url = "enrollments:exam_list"
    is_continue = True

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['prerequisite'].queryset = Exam.objects.filter(exam_type='mock', is_deleted=False)
        return form

class ExamUpdateView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, UpdateView):
    model = Exam
    template_name = "enrollments/exam_create.html"
    form_class = ExamForm

    def get_success_url(self):
        return reverse_lazy('enrollments:question_list', kwargs={'exam_id': self.object.id})
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['prerequisite'].queryset = Exam.objects.filter(
            exam_type='mock', is_deleted=False
        ).exclude(id=self.object.id)
        return form


# --- 問題管理 ---

class QuestionListView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, ListView):
    model = Question
    template_name = 'enrollments/question_list.html'
    context_object_name = 'questions'

    def get_queryset(self):
        return Question.objects.filter(exam_id=self.kwargs['exam_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['exam'] = get_object_or_404(Exam, pk=self.kwargs['exam_id'])
        context['exam_id'] = self.kwargs['exam_id']
        return context

class QuestionAddView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, ContextMixin, View):
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        context = self.get_context_data(exam=exam, form=QuestionForm(), formset=ChoiceFormSet(), exam_id=exam_id)
        return render(request, 'enrollments/question_form.html', context)

    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        form = QuestionForm(request.POST)
        formset = ChoiceFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            question = form.save(commit=False)
            question.exam = exam
            question.save()
            formset.instance = question
            formset.save()
            return redirect('enrollments:question_list', exam_id=exam.id)
        return render(request, 'enrollments/question_form.html', self.get_context_data(exam=exam, form=form, formset=formset, exam_id=exam_id))

class QuestionEditView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, ContextMixin, View):
    def get(self, request, question_id):
        question = get_object_or_404(Question, pk=question_id)
        context = self.get_context_data(exam=question.exam, form=QuestionForm(instance=question), formset=EditChoiceFormSet(instance=question), exam_id=question.exam.id, is_edit=True)
        return render(request, 'enrollments/question_form.html', context)

    def post(self, request, question_id):
        question = get_object_or_404(Question, pk=question_id)
        form = QuestionForm(request.POST, instance=question)
        formset = EditChoiceFormSet(request.POST, instance=question)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('enrollments:question_list', exam_id=question.exam.id)
        return render(request, 'enrollments/question_form.html', self.get_context_data(exam=question.exam, form=form, formset=formset, exam_id=question.exam.id, is_edit=True))

class QuestionDeleteView(AdminOrModeratorRequiredMixin, View):
    def post(self, request, question_id):
        question = get_object_or_404(Question, pk=question_id)
        exam_id = question.exam.id
        question.delete()
        return redirect('enrollments:question_list', exam_id=exam_id)


# --- 検定アクション ---

class ExamToggleActiveView(AdminOrModeratorRequiredMixin, View):
    """公開非公開をリアルタイムで切り替える"""
    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        exam.is_active = not exam.is_active
        exam.save()
        return JsonResponse({'status': 'success', 'is_active': exam.is_active})

class ExamDeleteView(AdminOrModeratorRequiredMixin, View):
    """個別削除（ゴミ箱へ移動）"""
    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        exam.is_deleted = True
        exam.save()
        if exam.exam_type == 'mock':
            Exam.objects.filter(prerequisite=exam).update(is_deleted=True)
        return redirect('enrollments:exam_list')

class ExamRestoreView(AdminOrModeratorRequiredMixin, View):
    """個別復元（ゴミ箱から戻す）"""
    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        exam.is_deleted = False
        exam.save()
        return redirect(f"{reverse_lazy('enrollments:exam_list')}?show=deleted")

class ExamBulkActionView(AdminOrModeratorRequiredMixin, View):
    """一括操作ロジック"""
    def post(self, request):
        exam_ids = request.POST.getlist('selected_exams')
        action = request.POST.get('action')
        restore_prerequisite = (request.POST.get('restore_prerequisite') == 'true')

        if not exam_ids:
            return redirect('enrollments:exam_list')

        target_exams = Exam.objects.filter(id__in=exam_ids)

        if action == 'delete':
            target_exams.update(is_deleted=True)
            mock_ids = Exam.objects.filter(id__in=exam_ids, exam_type='mock').values_list('id', flat=True)
            if mock_ids:
                Exam.objects.filter(prerequisite_id__in=mock_ids).update(is_deleted=True)
        elif action == 'restore':
            target_exams.update(is_deleted=False)
            if restore_prerequisite:
                prereq_ids = target_exams.filter(exam_type='main').values_list('prerequisite_id', flat=True)
                target_mocks = [pid for pid in prereq_ids if pid]
                Exam.objects.filter(id__in=target_mocks).update(is_deleted=False)
        elif action == 'make_public':
            target_exams.update(is_active=True)
        elif action == 'make_private':
            target_exams.update(is_active=False)
        
        return redirect('enrollments:exam_list')


# --- AI自動生成 ---

class AddQuestionAIView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, ContextMixin, View):
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        context = self.get_context_data(exam=exam)
        return render(request, 'enrollments/exam_ai_add.html', context)

    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        if not exam.exams_file:
            context = self.get_context_data(error='教材が登録されていません。', exam_id=exam_id)
            return render(request, 'enrollments/enrollments_error.html', context) 
        num_questions = request.POST.get('count', 5)
        difficulty = request.POST.get('difficulty', '中級')
        try:
            with exam.exams_file.open('rb') as f:
                file_data = f.read()
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(
                model_name="gemini-flash-latest",
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            prompt = f"教材内容から4択問題({num_questions}問、難易度:{difficulty})をJSON形式で作成してください..."
            response = model.generate_content([prompt, {'mime_type': 'application/pdf', 'data': file_data}])
            raw_text = response.text.replace('```json', '').replace('```', '').strip()
            quiz_data = json.loads(raw_text)
            if isinstance(quiz_data, dict): quiz_data = quiz_data.get('questions', [quiz_data])
            for item in quiz_data:
                q_text = item.get('text') or item.get('question')
                if q_text:
                    q = Question.objects.create(exam=exam, text=q_text)
                    choices = item.get('choices', [])
                    random.shuffle(choices)
                    for c in choices:
                        Choice.objects.create(question=q, text=c.get('text'), is_correct=c.get('is_correct', False))
            return redirect('enrollments:question_list', exam_id=exam.id)
        except Exception as e:
            return render(request, 'enrollments/enrollments_error.html', self.get_context_data(error=str(e), exam_id=exam_id))


# --- 受講者用 ---

class UserExamListView(BaseTemplateMixin, ListView):
    model = Exam
    template_name = "enrollments/exam_list_user.html"
    context_object_name = "exams"
    def get_queryset(self):
        return Exam.objects.filter(is_deleted=False, is_active=True).order_by('-created_at')

class ExamTakeView(BaseTemplateMixin, ContextMixin, View):
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id, is_active=True)
        if exam.exam_type == 'main' and exam.prerequisite:
            passed = UserExamStatus.objects.filter(user=request.user, exam=exam.prerequisite, is_passed=True).exists()
            if not passed: return render(request, 'enrollments/enrollments_error.html', self.get_context_data(error=f'先に「{exam.prerequisite.title}」に合格してください。', exam_id=exam.prerequisite.id))
        return render(request, 'enrollments/exam_take.html', self.get_context_data(exam=exam, questions=exam.questions.all().order_by('?')))

class ExamGradeView(BaseTemplateMixin, ContextMixin, View):
    """受講者の解答を採点し、結果を保存する"""
    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        questions = exam.questions.all()
        correct = 0
        for q in questions:
            choice_id = request.POST.get(f'question_{q.id}')
            if choice_id and Choice.objects.filter(pk=choice_id, is_correct=True).exists():
                correct += 1
        
        total = questions.count()
        score = int(round((correct / total) * 100)) if total > 0 else 0
        is_passed = score >= exam.passing_score

        if is_passed:
            status, _ = UserExamStatus.objects.get_or_create(user=request.user, exam=exam)
            status.is_passed = True
            status.save()

        return render(request, 'enrollments/exam_result.html', self.get_context_data(
            exam=exam, 
            score=score, 
            is_passed=is_passed, 
            correct_count=correct, 
            total=total
        ))