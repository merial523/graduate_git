from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from main.models import Exam, Question, Badge 
from .forms import QuestionForm, ChoiceFormSet


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

# 2. 検定作成（タイトル登録）
class ExamCreateView(CreateView):
    model = Exam
    fields = ["title", "description", "passing_score"] 
    template_name = "enrollments/exam_create.html" # 名前を変更
    success_url = reverse_lazy("enrollments:exam_list") 

# 3. 問題追加（1問ずつ登録）
def add_question(request, exam_id):
    # (1) どの検定に問題を追加するか、URLのIDから特定
    exam = get_object_or_404(Exam, pk=exam_id)
    
    if request.method == "POST":
        # (2) 送信されたデータ（問題文と複数の選択肢）を受け取る
        form = QuestionForm(request.POST)
        formset = ChoiceFormSet(request.POST)
        
        # (3) 両方の入力内容が正しいかチェック
        if form.is_valid() and formset.is_valid():
            # --- 問題(Question)の保存 ---
            question = form.save(commit=False) # まだDBに保存しない
            question.exam = exam                # この問題は「この検定」のものだと紐付け
            question.save()                     # DBに保存
            
            # --- 選択肢(Choice)の保存 ---
            formset.instance = question         # この選択肢たちは「この問題」のものだと紐付け
            formset.save()                      # DBに一括保存
            
            # (4) 保存後の動き
            # 「続けて登録」ボタンが押された場合は、再度このページを表示
            if "add_another" in request.POST:
                return redirect('enrollments:add_question', exam_id=exam.id)
            
            # それ以外は一覧画面へ戻る
            return redirect('enrollments:exam_list')
    else:
        # (5) 最初に画面を開いた時（空のフォームを表示）
        form = QuestionForm()
        formset = ChoiceFormSet()
        
    return render(request, 'enrollments/question_form.html', {
        'exam': exam,
        'form': form,
        'formset': formset,
    })