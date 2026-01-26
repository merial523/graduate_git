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
    form_class = ExamForm
    is_continue = True

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['prerequisite'].queryset = Exam.objects.filter(exam_type='mock', is_deleted=False)
        return form

    def form_valid(self, form):
        # 1. 新規アップロードがあるか確認
        new_file = self.request.FILES.get('exams_file')
        # 2. 過去のファイル選択（プルダウン）の値を確認
        past_file_name = form.cleaned_data.get('exam_file')

        if new_file:
            # 新規があればそのまま（Djangoが自動保存）
            pass
        elif past_file_name:
            # 新規がなく、過去のファイルが選択されていれば、そのパスをセット
            # ※ ファイルパスは 'exams_files/ファイル名' の形式で保存されます
            form.instance.exams_file.name = f"exams_files/{past_file_name}"
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('enrollments:question_list', kwargs={'exam_id': self.object.id})


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

    def form_valid(self, form):
        # 編集時も同様のロジック（新規があれば上書き、なければ既存維持）
        new_file = self.request.FILES.get('exams_file')
        past_file_name = form.cleaned_data.get('exam_file')

        if new_file:
            pass
        elif past_file_name:
            # プルダウンで別の過去ファイルを選び直した場合
            form.instance.exams_file.name = f"exams_files/{past_file_name}"
            
        return super().form_valid(form)


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