import json
import random
import os
import fitz  # type: ignore
import google.generativeai as genai  # type: ignore
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
# ★ ContextMixin をインポートに追加
from django.views.generic.base import ContextMixin 
from django.views.generic import ListView, UpdateView, TemplateView
from django.urls import reverse_lazy
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

    def get_queryset(self):
        self.is_trash_mode = self.request.GET.get("show") == "deleted"
        queryset = Exam.objects.filter(is_active=not self.is_trash_mode)
        sort = self.request.GET.get('sort', 'newest')
        sort_dict = {'newest': '-created_at', 'oldest': 'created_at', 'title': 'title'}
        return queryset.order_by(sort_dict.get(sort, '-created_at'))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_trash_mode'] = self.is_trash_mode
        context['current_sort'] = self.request.GET.get('sort', 'newest')
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
        form.fields['prerequisite'].queryset = Exam.objects.filter(exam_type='mock', is_active=True)
        return form
    
    def form_valid(self, form):
        existing = form.cleaned_data.get('exam_file')
        if existing and not self.request.FILES.get('exams_file'):
            form.instance.exams_file.name = f"exams_files/{existing}"
        return super().form_valid(form)

class ExamUpdateView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, UpdateView):
    model = Exam
    template_name = "enrollments/exam_create.html"
    form_class = ExamForm

    def get_success_url(self):
        return reverse_lazy('enrollments:question_list', kwargs={'exam_id': self.object.id})
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['prerequisite'].queryset = Exam.objects.filter(
            exam_type='mock', is_active=True
        ).exclude(id=self.object.id)
        return form

    def form_valid(self, form):
        existing = form.cleaned_data.get('exam_file')
        if existing and not self.request.FILES.get('exams_file'):
            form.instance.exams_file.name = f"exams_files/{existing}"
        return super().form_valid(form)


# --- 問題管理（ContextMixin を追加してエラーを回避） ---

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

# ★ ContextMixin を継承に加えることで AttributeError を防ぎます
class QuestionAddView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, ContextMixin, View):
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        # Mixinの get_context_data が呼べるようになります
        context = self.get_context_data(
            exam=exam, form=QuestionForm(), formset=ChoiceFormSet(), exam_id=exam_id
        )
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
            if "add_another" in request.POST:
                return redirect('enrollments:add_question', exam_id=exam.id)
            return redirect('enrollments:question_list', exam_id=exam.id)
        return render(request, 'enrollments/question_form.html', self.get_context_data(exam=exam, form=form, formset=formset, exam_id=exam_id))

class QuestionEditView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, ContextMixin, View):
    def get(self, request, question_id):
        question = get_object_or_404(Question, pk=question_id)
        context = self.get_context_data(
            exam=question.exam, form=QuestionForm(instance=question),
            formset=EditChoiceFormSet(instance=question), exam_id=question.exam.id, is_edit=True
        )
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

class ExamDeleteView(AdminOrModeratorRequiredMixin, View):
    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        exam.is_active = False
        exam.save()
        Badge.objects.filter(exam=exam).update(is_active=False)

        # メイン検定の場合、関連する模擬検定も非アクティブ化
        if exam.exam_type == 'main':
            mock_exams = Exam.objects.filter(prerequisite=exam, is_active=True)
            for mock in mock_exams:
                mock.is_active = False
                mock.save()
                Badge.objects.filter(exam=mock).update(is_active=False)

        return redirect('enrollments:exam_list')

class ExamRestoreView(AdminOrModeratorRequiredMixin, View):
    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        exam.is_active = True
        exam.save()
        Badge.objects.filter(exam=exam).update(is_active=True)

        #仮検定を復元する場合、関連するメイン検定もアクティブ化
        if exam.exam_type == 'mock':
            # 自分が prerequisite に設定されている他の検定（本試験）を取得
            dependent_exams = Exam.objects.filter(prerequisite=exam)
            # それらを一括で復元
            dependent_exams.update(is_active=True)
            # それらのバッジも一括で復元
            Badge.objects.filter(exam__in=dependent_exams).update(is_active=True)


        # メイン検定の場合、関連する模擬検定もアクティブ化
        if exam.exam_type == 'main' and exam.prerequisite and not exam.prerequisite.is_active:
            exam.prerequisite.is_active = True
            exam.prerequisite.save()
            Badge.objects.filter(exam=exam.prerequisite).update(is_active=True)

        return redirect(f"{reverse_lazy('enrollments:exam_list')}?show=deleted")

class ExamBulkActionView(AdminOrModeratorRequiredMixin, View):
    def post(self, request):
        exam_ids = request.POST.getlist('selected_exams')
        action = request.POST.get('action')
        if exam_ids:
            # 共通のフラグ設定 (restoreならTrue, deleteならFalse)
            is_active_value = (action == 'restore')
            
            # 1. 選択された検定自体を一括更新
            Exam.objects.filter(id__in=exam_ids).update(is_active=is_active_value)
            Badge.objects.filter(exam_id__in=exam_ids).update(is_active=is_active_value)

            # --- 連動処理A: 【本試験 → 仮試験】への影響 ---
            # 選択された「本試験」が持つ「前提の仮試験(prerequisite)」のIDを抽出
            related_mock_ids = Exam.objects.filter(
                id__in=exam_ids, 
                exam_type='main'
            ).values_list('prerequisite_id', flat=True)
            
            # Noneを除外して一括更新
            mock_ids = [rid for rid in related_mock_ids if rid is not None]
            if mock_ids:
                Exam.objects.filter(id__in=mock_ids).update(is_active=is_active_value)
                Badge.objects.filter(exam_id__in=mock_ids).update(is_active=is_active_value)

            # --- 連動処理B: 【仮試験 → 本試験】への影響 ---
            # 選択された「仮試験」を前提にしている「本試験」のIDを抽出
            # ※これが「仮試験のみ削除した時に本試験も消す」ためのロジックです
            selected_mock_ids = Exam.objects.filter(
                id__in=exam_ids, 
                exam_type='mock'
            ).values_list('id', flat=True)
            
            if selected_mock_ids:
                # これらの仮試験を前提(prerequisite)としている本試験を探す
                dependent_main_ids = Exam.objects.filter(
                    prerequisite_id__in=selected_mock_ids
                ).values_list('id', flat=True)
                
                if dependent_main_ids:
                    # 連動する本試験たちも一括更新（削除・復元の両方に対応）
                    Exam.objects.filter(id__in=dependent_main_ids).update(is_active=is_active_value)
                    Badge.objects.filter(exam_id__in=dependent_main_ids).update(is_active=is_active_value)

            # 復元時はゴミ箱画面へ、削除時は通常一覧へリダイレクト
            if action == 'restore':
                return redirect(f"{reverse_lazy('enrollments:exam_list')}?show=deleted")
        
        return redirect('enrollments:exam_list')
class AddQuestionAIView(AdminOrModeratorRequiredMixin, BaseTemplateMixin, ContextMixin, View):
    """AIによる問題自動生成（セーフティフィルター緩和・エラー対策済み版）"""
    
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        context = self.get_context_data(exam=exam)
        return render(request, 'enrollments/exam_ai_add.html', context)

    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        
        # 教材の存在チェック
        if not exam.exams_file:
            context = self.get_context_data(error='教材が登録されていません。', exam_id=exam_id)
            return render(request, 'enrollments/enrollments_error.html', context) 
        
        num_questions = request.POST.get('count', 5)
        difficulty = request.POST.get('difficulty', '中級')

        try:
            # 1. 教材データを読み込み
            with exam.exams_file.open('rb') as f:
                file_data = f.read()

            # 2. AIの設定
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # ★ 修正ポイント：セーフティ設定を追加して「回答拒否」を防ぐ
            model = genai.GenerativeModel(
                model_name="gemini-flash-latest",
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            # 3. 厳格なプロンプトの定義
            prompt = f"""
                以下の教材内容から、4択形式の検定問題を「{num_questions}問」作成してください。
                問題の難易度は「{difficulty}」にしてください。

                【重要：JSONの構造ルール】
                出力は必ず、以下の構造を持つJSON形式のリストのみで返してください。
                キーの名前（text, choices, is_correct）は、一字一句違わず以下の通りに指定すること。

                [
                {{
                    "text": "問題文をここに書く",
                    "choices": [
                    {{"text": "正解の選択肢", "is_correct": true}},
                    {{"text": "間違いの選択肢1", "is_correct": false}},
                    {{"text": "間違いの選択肢2", "is_correct": false}},
                    {{"text": "間違いの選択肢3", "is_correct": false}}
                    ]
                }}
                ]

                【禁止事項】
                1. JSON以外の説明文、挨拶などは一切含めないこと。
                2. 正解（is_correct: true）の位置は、ランダムに配置すること。
            """

            # 4. AIへのリクエスト
            response = model.generate_content([
                prompt, 
                {'mime_type': 'application/pdf', 'data': file_data}
            ])

            # 5. 解析処理（JSONのクリーニング）
            raw_text = response.text.replace('```json', '').replace('```', '').strip()
            quiz_data = json.loads(raw_text)

            # データが単一辞書ならリストに包む（型エラー対策）
            if isinstance(quiz_data, dict):
                quiz_data = quiz_data.get('questions', [quiz_data])

            # 6. データベースへの保存
            for item in quiz_data:
                # 'text'がなくても 'question' 等で探す（KeyError対策）
                q_text = item.get('text') or item.get('question') or item.get('question_text')
                if not q_text:
                    continue

                q = Question.objects.create(exam=exam, text=q_text)

                # 選択肢の取得
                choices_data = item.get('choices') or item.get('options')
                if not choices_data:
                    continue

                # シャッフルして保存
                random.shuffle(choices_data)
                for c in choices_data:
                    c_text = c.get('text') or c.get('content') or c.get('option')
                    if c_text:
                        Choice.objects.create(
                            question=q, 
                            text=c_text, 
                            is_correct=c.get('is_correct', False)
                        )
            
            return redirect('enrollments:question_list', exam_id=exam.id)

        except Exception as e:
            # エラーの詳細を error.html に送る
            context = self.get_context_data(error=str(e), exam_id=exam_id)
            return render(request, 'enrollments/enrollments_error.html', context)

# --- 受講者用 ---

class UserExamListView(BaseTemplateMixin, ListView):
    model = Exam
    template_name = "enrollments/exam_list_user.html"
    context_object_name = "exams"

    def get_queryset(self):
        return Exam.objects.filter(is_active=True).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['passed_exam_ids'] = UserExamStatus.objects.filter(
            user=self.request.user, is_passed=True
        ).values_list('exam_id', flat=True)
        return context

class ExamTakeView(BaseTemplateMixin, ContextMixin, View):
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id, is_active=True)
        if exam.exam_type == 'main' and exam.prerequisite:
            passed = UserExamStatus.objects.filter(user=request.user, exam=exam.prerequisite, is_passed=True).exists()
            if not passed:
                return render(request, 'enrollments/enrollments_error.html', self.get_context_data(error=f'先に「{exam.prerequisite.title}」に合格してください。', exam_id=exam.prerequisite.id))
        
        return render(request, 'enrollments/exam_take.html', self.get_context_data(exam=exam, questions=exam.questions.all().order_by('?')))

class ExamGradeView(BaseTemplateMixin, ContextMixin, View):
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

        return render(request, 'enrollments/exam_result.html', self.get_context_data(exam=exam, score=score, is_passed=is_passed, correct_count=correct, total=total))