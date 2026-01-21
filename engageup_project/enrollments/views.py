import json
import random
import os
import fitz  # type: ignore
import google.generativeai as genai  # type: ignore
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, UpdateView
from django.urls import reverse_lazy
from common.views import BaseCreateView
from main.models import Exam, Question, Badge, Choice, UserExamStatus
from .forms import QuestionForm, ChoiceFormSet, EditChoiceFormSet, ExamForm

# --- 基本表示 ---

def enrollments_index(request):
    """トップページ表示"""
    return render(request, "enrollments/5101.html")

def enrollments_history(request):
    """受験履歴表示"""
    return render(request, "enrollments/enrollments_history.html")


# --- 検定管理（管理者・モデレーター用） ---

class ExamListView(ListView):
    """検定一覧（管理用）：並べ替え、論理削除の表示切り替えに対応"""
    model = Exam
    template_name = "enrollments/all_enrollments.html"
    context_object_name = "exams"

    def get_queryset(self):
        # URLのパラメータ show=deleted を確認
        self.is_trash_mode = self.request.GET.get("show") == "deleted"
        
        # 表示対象をフィルタリング
        queryset = Exam.objects.filter(is_active=not self.is_trash_mode)

        # 並べ替えの適用
        sort = self.request.GET.get('sort', 'newest')
        sort_dict = {
            'newest': '-created_at',
            'oldest': 'created_at',
            'title': 'title',
        }
        order_by = sort_dict.get(sort, '-created_at')
        return queryset.order_by(order_by)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_trash_mode'] = self.is_trash_mode
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        return context

class ExamCreateView(BaseCreateView):
    """新規検定作成"""
    model = Exam
    template_name = "enrollments/exam_create.html"
    success_url = reverse_lazy("enrollments:exam_list") 
    form_class = ExamForm

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # prerequisite（前提試験）の選択肢を「仮試験（mock）」かつ「有効なもの」だけに絞る
        form.fields['prerequisite'].queryset = Exam.objects.filter(exam_type='mock', is_active=True)
        return form
    
    def form_valid(self, form):
        # 選択された保存済み教材ファイルがあれば設定
        exam_file = form.cleaned_data.get('exam_file')
        if exam_file:
            form.instance.exams_file.name = os.path.join('exams_files', exam_file)
        return super().form_valid(form)
    
    

class ExamUpdateView(UpdateView):
    """検定設定および教材の編集"""
    model = Exam
    template_name = "enrollments/exam_create.html"
    form_class = ExamForm

    def get_success_url(self):
        return reverse_lazy('enrollments:question_list', kwargs={'exam_id': self.object.id})
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # 選択肢を「仮試験」だけに絞る
        form.fields['prerequisite'].queryset = Exam.objects.filter(
            exam_type='mock', 
            is_active=True
        ).exclude(id=self.object.id)
        return form
    
    def form_valid(self, form):
        # 選択された保存済み教材ファイルがあれば設定
        exam_file = form.cleaned_data.get('exam_file')
        if exam_file:
            form.instance.exams_file.name = os.path.join('exams_files', exam_file)
        return super().form_valid(form)


# --- 問題管理（手動操作） ---

def question_list(request, exam_id):
    """特定検定の問題一覧を表示"""
    exam = get_object_or_404(Exam, pk=exam_id)
    questions = exam.questions.all() 
    return render(request, 'enrollments/question_list.html', {'exam': exam, 'questions': questions})

def add_question(request, exam_id):
    """手動で問題を1問追加（選択肢とセット）"""
    exam = get_object_or_404(Exam, pk=exam_id)
    if request.method == "POST":
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
    else:
        form = QuestionForm()
        formset = ChoiceFormSet()
    return render(request, 'enrollments/question_form.html', {
        'exam': exam, 'form': form, 'formset': formset, 'exam_id': exam_id
    })

def edit_question(request, question_id):
    """既存の問題と選択肢を編集"""
    question = get_object_or_404(Question, pk=question_id)
    exam = question.exam 

    if request.method == "POST":
        form = QuestionForm(request.POST, instance=question)
        formset = EditChoiceFormSet(request.POST, instance=question)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('enrollments:question_list', exam_id=exam.id)
    else:
        form = QuestionForm(instance=question)
        formset = EditChoiceFormSet(instance=question)
        
    return render(request, 'enrollments/question_form.html', {
        'exam': exam, 'form': form, 'formset': formset, 'exam_id': exam.id, 'is_edit': True
    })

def delete_question(request, question_id):
    """問題を完全に削除"""
    question = get_object_or_404(Question, pk=question_id)
    exam_id = question.exam.id
    if request.method == "POST":
        question.delete()
    return redirect('enrollments:question_list', exam_id=exam_id)


# --- 検定の一括操作・論理削除 ---

def delete_exam(request, exam_id):
    """検定を論理削除（非表示化）"""
    exam = get_object_or_404(Exam, pk=exam_id)
    if request.method == "POST":
        exam.is_active = False
        exam.save()
    return redirect('enrollments:exam_list')

def restore_exam(request, exam_id):
    """論理削除された検定を復元"""
    exam = get_object_or_404(Exam, pk=exam_id)
    if request.method == "POST":
        exam.is_active = True
        exam.save()
    return redirect(f"{reverse_lazy('enrollments:exam_list')}?show=deleted")

def bulk_action_exam(request):
    """複数の検定を一括で論理削除または復元"""
    if request.method == "POST":
        exam_ids = request.POST.getlist('selected_exams')
        action = request.POST.get('action')
        if exam_ids:
            if action == 'delete':
                Exam.objects.filter(id__in=exam_ids).update(is_active=False)
            elif action == 'restore':
                Exam.objects.filter(id__in=exam_ids).update(is_active=True)
                return redirect(f"{reverse_lazy('enrollments:exam_list')}?show=deleted")
    return redirect('enrollments:exam_list')


# --- AI問題自動生成 ---

# --- AI問題自動生成（難易度指定対応版） ---

def add_question_ai(request, exam_id):
    """Gemini APIを使用して教材から問題を自動生成（難易度・問題数指定対応）"""
    exam = get_object_or_404(Exam, pk=exam_id)
    if not exam.exams_file:
        return render(request, 'enrollments/enrollments_error.html', {'error': '教材が登録されていません', 'exam_id': exam_id}) 

    if request.method == "POST":
        # フォームから問題数と難易度を取得
        num_questions = request.POST.get('count', 5)
        difficulty = request.POST.get('difficulty', '中級（標準的なレベル）') 

        try:
            # 教材データの読み込み
            with exam.exams_file.open('rb') as f:
                file_data = f.read()

            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-flash-latest")
            
            # AIへの指示文（プロンプト）を構築
            prompt = f"""
            以下の教材内容から、4択形式の検定問題を「{num_questions}問」作成してください。
            
            【指定の難易度】
            {difficulty}
            
            【基本ルール】
            1. 出力は必ず以下のJSON形式のリストのみで返してください。余計な文章は含めないでください。
            2. 正解(is_correct: true)の位置は、1番目〜4番目の中でランダムに配置してください。

            [
              {{
                "text": "問題文",
                "choices": [
                  {{"text": "選択肢1", "is_correct": true}},
                  {{"text": "選択肢2", "is_correct": false}},
                  {{"text": "選択肢3", "is_correct": false}},
                  {{"text": "選択肢4", "is_correct": false}}
                ]
              }}
            ]
            """
            
            # AIへのリクエスト実行（教材とプロンプトを同時送信）
            response = model.generate_content([prompt, {'mime_type': 'application/pdf', 'data': file_data}])
            
            # JSON解析
            raw_json = response.text.replace('```json', '').replace('```', '').strip()
            quiz_data = json.loads(raw_json)

            # データベース保存
            for item in quiz_data:
                q = Question.objects.create(exam=exam, text=item['text'])
                choices = item['choices']
                random.shuffle(choices) # 保存前にさらにランダム化
                for c in choices:
                    Choice.objects.create(question=q, text=c['text'], is_correct=c['is_correct'])
            
            return redirect('enrollments:question_list', exam_id=exam.id)
        
        except Exception as e:
            return render(request, 'enrollments/enrollments_error.html', {'error': str(e), 'exam_id': exam_id})

    return render(request, 'enrollments/exam_ai_add.html', {'exam': exam})


# --- 受講者用機能：受験・採点 ---

def user_exam_list(request):
    """受講者用：公開中の検定一覧（合格済みの判定付き）"""
    exams = Exam.objects.filter(is_active=True).order_by('-created_at')
    passed_exam_ids = UserExamStatus.objects.filter(user=request.user, is_passed=True).values_list('exam_id', flat=True)

    return render(request, 'enrollments/exam_list_user.html', {
        'exams': exams, 'passed_exam_ids': passed_exam_ids,
    })

def exam_take(request, exam_id):
    """受講者用：試験画面（本試験のロック判定あり）"""
    exam = get_object_or_404(Exam, pk=exam_id, is_active=True)
    
    # 本試験の前提条件（仮試験合格）チェック
    if exam.exam_type == 'main' and exam.prerequisite:
        has_passed_mock = UserExamStatus.objects.filter(user=request.user, exam=exam.prerequisite, is_passed=True).exists()
        if not has_passed_mock:
            return render(request, 'enrollments/enrollments_error.html', {
                'error': f'この試験を受けるには、まず「{exam.prerequisite.title}」に合格する必要があります。',
                'exam_id': exam.prerequisite.id
            })
    
    questions = exam.questions.all()
    return render(request, 'enrollments/exam_take.html', {'exam': exam, 'questions': questions})

def exam_grade(request, exam_id):
    """受講者用：採点処理および合格ステータスの記録"""
    exam = get_object_or_404(Exam, pk=exam_id)
    questions = exam.questions.all()
    correct_count = 0
    total = questions.count()

    if request.method == "POST":
        for q in questions:
            choice_id = request.POST.get(f'question_{q.id}')
            if choice_id and Choice.objects.get(pk=choice_id).is_correct:
                correct_count += 1
        
        # 100点満点の整数スコア算出
        score = int(round((correct_count / total) * 100)) if total > 0 else 0
        is_passed = score >= exam.passing_score

        # 合格した場合、合格実績を保存または更新
        if is_passed:
            status, _ = UserExamStatus.objects.get_or_create(user=request.user, exam=exam)
            status.is_passed = True
            status.save()

        return render(request, 'enrollments/exam_result.html', {
            'exam': exam, 'score': score, 'is_passed': is_passed,
            'correct_count': correct_count, 'total': total
        })