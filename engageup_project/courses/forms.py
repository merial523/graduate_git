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
    # タイトルを明示的に定義（必須バリデーションを確実に有効化）
    title = forms.CharField(
        label="研修モジュールタイトル",
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'required': 'required',
            'placeholder': '研修のタイトルを入力してください'
        })
    )
    
    existing_file = forms.ChoiceField(
        choices=[], 
        required=False, 
        label="保存済みライブラリから選ぶ",

        widget=forms.Select(attrs={'class': 'form-select'}))
        #テキストをpdfのみに制限をかける

    training_file = forms.FileField(
        label="研修ファイルをアップロード",
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,'  # PDFおよびテキストファイルのみ許可
        }))
    
    #動画の形式の制限（.mp4,.mov,.avi）
    video = forms.FileField(
        label="研修動画をアップロード",
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.mp4,.mov,.avi'  # 動画ファイル形式を制限
        })

    )

    class Meta:
        model = TrainingModule
        fields = ["title", "video", "training_file", "content_text", "estimated_time"]
        widgets = {
            'content_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'estimated_time': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        def clean_video(self):
            video = self.cleaned_data.get('video')
            if video:
                # 許可する拡張子のリスト
                valid_extensions = ['.mp4', '.mov', '.avi']
                # ファイル名から拡張子を取り出して小文字にする
                ext = os.path.splitext(video.name)[1].lower()
                if ext not in valid_extensions:
                    raise forms.ValidationError("動画は .mp4, .mov, .avi 形式のみアップロード可能です。")
            return video

    # サーバー側での教材ファイル最終チェック（以前の分）
    def clean_training_file(self):
        file = self.cleaned_data.get('training_file')
        if file:
            if not file.name.lower().endswith('.pdf'):
                raise forms.ValidationError("教材資料はPDFファイルのみアップロード可能です。")
        return file

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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