import json
import random
import fitz  # type: ignore # PyMuPDF
import os
import google.generativeai as genai # type: ignore
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from main.models import Exam, Question, Badge ,Choice
from .forms import QuestionForm, ChoiceFormSet, EditChoiceFormSet


def enrollments_index(request):
    return render(
request, "enrollments/5101.html"
)  # アプリ内 templates/enrollments/index.html を参照

def enrollments_history(request):
    return render(
        request, "enrollments/enrollments_history.html"
    )  # アプリ内 templates/enrollments/enrollments_history.html を参照


# --- 検定管理（モデレーター用） ---

# 1. 検定の一覧画面
class ExamListView(ListView):
    model = Exam
    template_name = "enrollments/all_enrollments.html"  # 名前を変更
    context_object_name = "exams"

    def get_queryset(self):
        self.is_trash_mode = self.request.GET.get("show") == "deleted"
        if self.is_trash_mode:
            return Exam.objects.filter(is_active=False)
        return Exam.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_trash_mode'] = self.is_trash_mode
        return context
    

# 2. 検定作成（タイトル登録）
class ExamCreateView(CreateView):
    model = Exam
    fields = ["title", "description", "passing_score","exams_file"]  # 教材ファイルを追加
    template_name = "enrollments/exam_create.html" # 名前を変更
    success_url = reverse_lazy("enrollments:exam_list") 

class ExamUpdateView(UpdateView):
    model = Exam
    fields = ["title", "description", "passing_score", "exams_file"]
    template_name = "enrollments/exam_create.html" # 作成画面と同じテンプレートを使い回せます
    
    def get_success_url(self):
        # 編集が終わったら、その検定の問題一覧に戻る
        return reverse_lazy('enrollments:question_list', kwargs={'exam_id': self.object.id})

# 3. 問題追加（1問ずつ登録）
def add_question(request, exam_id):
    #どの検定に問題を追加するか、URLのIDから特定
    exam = get_object_or_404(Exam, pk=exam_id)
    
    if request.method == "POST":
        #送信されたデータ（問題文と複数の選択肢）を受け取る
        form = QuestionForm(request.POST)
        formset = ChoiceFormSet(request.POST)
        
        #両方の入力内容が正しいかチェック
        if form.is_valid() and formset.is_valid():
            # --- 問題(Question)の保存 ---
            question = form.save(commit=False) # まだDBに保存しない
            question.exam = exam                # この問題は「この検定」のものだと紐付け
            question.save()                     # DBに保存
            
            # --- 選択肢(Choice)の保存 ---
            formset.instance = question         # この選択肢たちは「この問題」のものだと紐付け
            formset.save()                      # DBに一括保存
            
            #保存後の動き
            # 「続けて登録」ボタンが押された場合は、再度このページを表示
            if "add_another" in request.POST:
                return redirect('enrollments:add_question', exam_id=exam.id)
            
            # それ以外は一覧画面へ戻る
            return redirect('enrollments:exam_list')
    else:
        #最初に画面を開いた時（空のフォームを表示）
        form = QuestionForm()
        formset = ChoiceFormSet()
        
    return render(request, 'enrollments/question_form.html', {
        'exam': exam,
        'form': form,
        'formset': formset,
        'exam_id': exam_id,
    })

    # ---問題の一覧を表示する ---
def question_list(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    # 紐付いている問題をすべて取得（related_name='questions' を活用）
    questions = exam.questions.all() 
    return render(request, 'enrollments/question_list.html', {
        'exam': exam,
        'questions': questions,
    })

# ---既存の問題を編集する ---
def edit_question(request, question_id):
    # 修正したい問題を特定
    question = get_object_or_404(Question, pk=question_id)
    exam = question.exam 

    if request.method == "POST":
        form = QuestionForm(request.POST, instance=question)
        formset = EditChoiceFormSet(request.POST, instance=question)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            # 編集が終わったら、その検定の問題一覧画面に戻る
            return redirect('enrollments:question_list', exam_id=exam.id)
    else:
        # 既存のデータをフォームに初期値として入れる
        form = QuestionForm(instance=question)
        formset = EditChoiceFormSet(instance=question)
        
    return render(request, 'enrollments/question_form.html', { # 登録と同じテンプレートを使い回せます
        'exam': exam,
        'form': form,
        'formset': formset,
        'exam_id': exam.id,
        'is_edit': True, # テンプレート側で「編集」と表示を切り替えるためのフラグ
    })

# --- 問題を削除する (物理)　---
def delete_question(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    exam_id = question.exam.id
    if request.method == "POST":
        question.delete()
    return redirect('enrollments:question_list', exam_id=exam_id)

# --- 検定削除　（論理） ---
def delete_exam(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    if request.method == "POST":
        exam.is_active = False  # データは消さずに非表示にするだけ
        exam.save()
    return redirect('enrollments:exam_list')


# --- 検定削除一括操作：1個でも複数でもOK ---
def bulk_action_exam(request):
    if request.method == "POST":
        exam_ids = request.POST.getlist('selected_exams')
        action = request.POST.get('action') # "delete" か "restore"
        
        if exam_ids:
            if action == 'delete':
                # まとめて論理削除
                Exam.objects.filter(id__in=exam_ids).update(is_active=False)
                return redirect('enrollments:exam_list')
            elif action == 'restore':
                # まとめて復元
                Exam.objects.filter(id__in=exam_ids).update(is_active=True)
                return redirect(f"{reverse_lazy('enrollments:exam_list')}?show=deleted")
                
    return redirect('enrollments:exam_list')

def add_question_ai(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)

    if not exam.exams_file:
        return render(request, 'enrollments/enrollments_error.html', {'error': '教材がありません', 'exam_id': exam_id}) 

    if request.method == "POST":
        # 画面から入力された問題数を取得（送られてこなければ5にする）
        num_questions = request.POST.get('count', 5)
        
        try:
            # 1. テキスト抽出
            text_content = ""
            with exam.exams_file.open('rb') as f:
                doc = fitz.open(stream=f.read(), filetype="pdf")
                for page in doc:
                    text_content += page.get_text()

            # 2. AIの設定
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-flash-latest")
                        
            # プロンプトに num_questions を埋め込む
            prompt = f"""
            以下の教材内容から、4択形式の検定問題を「{num_questions}問」作成してください。
            【重要ルール】
            1. 出力は必ず以下のJSON形式のリストのみで返してください。
            2. 正解(is_correct: true)の位置は、1番目〜4番目の中でランダムに配置してください。
            
            [
            {{
                "text": "問題文",
                "choices": [
                {{"text": "正解", "is_correct": true}},
                {{"text": "間違い1", "is_correct": false}},
                {{"text": "間違い2", "is_correct": false}},
                {{"text": "間違い3", "is_correct": false}}
                ]
            }}
            ]
            教材: {text_content[:8000]}
            """

            # 3. 生成・保存処理
            response = model.generate_content(prompt)
            raw_json = response.text.replace('```json', '').replace('```', '').strip()
            quiz_data = json.loads(raw_json)

            for item in quiz_data:
                q = Question.objects.create(exam=exam, text=item['text'])
                choices = item['choices']
                random.shuffle(choices)
                for c in item['choices']:
                    Choice.objects.create(question=q, text=c['text'], is_correct=c['is_correct'])

            return redirect('enrollments:question_list', exam_id=exam.id)

        except Exception as e:
            return render(request, 'enrollments/enrollments_error.html', {'error': str(e)})

    return render(request, 'enrollments/exam_ai_add.html', {'exam': exam})

