from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from django.core.exceptions import ValidationError
import random


# =========================
# ユーティリティ関数
# =========================
def random_num():
    """
    会員番号を生成
    ※ 簡易的なランダム生成（本番運用ではユニーク制約の衝突ハンドリングが必要）
    """
    return random.randint(1000000000000, 10000000000000)


# =========================
# 定数テーブル
# =========================
class Constant(models.Model):
    company_code = models.CharField(
        verbose_name="会社コード", max_length=20, default="com"
    )
    address = models.CharField(
        verbose_name="アドレス", max_length=20, default="gmail.com"
    )

    def __str__(self):
        return self.company_code


# =========================
# 講座 (Course)
# =========================
class Course(models.Model):
    subject = models.CharField(verbose_name="講座名", max_length=50)
    courseCount = models.IntegerField(verbose_name="講座数", default=0)  # default追加
    is_active = models.BooleanField(verbose_name="有効かどうか", default=True)
    is_deleted = models.BooleanField(verbose_name="削除フラグ", default=False)

    def __str__(self):
        return self.subject


# =========================
# 研修モジュール (TrainingModule)
# =========================
class TrainingModule(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="modules",
        verbose_name="所属コース",
    )
    title = models.CharField(verbose_name="研修名", max_length=100)
    video = models.FileField(
        verbose_name="研修動画", upload_to="training_videos/", null=True, blank=True
    )
    training_file = models.FileField(
        verbose_name="要約元資料(PDF/画像)",
        upload_to="exams_files/",
        null=True,
        blank=True,
    )
    estimated_time = models.PositiveIntegerField(
        verbose_name="推奨学習時間(分)",
        default=30,
        help_text="受講者がこの研修を終えるのにかかる目安の時間（分）です",
    )
    content_text = models.TextField(verbose_name="研修テキスト", blank=True)
    order = models.IntegerField(verbose_name="表示順", default=0)
    is_active = models.BooleanField(verbose_name="有効フラグ", default=True)

    def __str__(self):
        return f"{self.course.subject} - {self.title}"


# =========================
# ユーザーの学習進捗 (UserModuleProgress)
# =========================
class UserModuleProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    module = models.ForeignKey(TrainingModule, on_delete=models.CASCADE)
    last_position = models.FloatField(default=0.0, verbose_name="再生位置(秒)")
    is_completed = models.BooleanField(default=False, verbose_name="完了フラグ")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "module")

    def __str__(self):
        status = "完了" if self.is_completed else "進行中"
        return f"{self.user.username} - {self.module.title} ({status})"


# =========================
# 研修内の例題 (Example)
# =========================
class TrainingExample(models.Model):
    module = models.ForeignKey(
        TrainingModule,
        on_delete=models.CASCADE,
        related_name="examples",
        verbose_name="対象研修",
    )
    text = models.TextField(verbose_name="例題文")
    explanation = models.TextField(verbose_name="解説", blank=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"例題: {self.text[:20]}"


class TrainingExampleChoice(models.Model):
    example = models.ForeignKey(
        TrainingExample, on_delete=models.CASCADE, related_name="choices"
    )
    text = models.CharField(verbose_name="選択肢", max_length=200)
    is_correct = models.BooleanField(verbose_name="これが正解か", default=False)

    def __str__(self):
        return self.text


# =========================
# お知らせ (News)
# =========================
class News(models.Model):
    CATEGORY_CHOICES = [
        ("news", "一般"),
        ("training", "復習通知"),
        ("urgent", "重要告知"),
    ]

    title = models.CharField(max_length=200, verbose_name="タイトル")
    content = models.TextField(verbose_name="内容")
    is_active = models.BooleanField(default=True, verbose_name="公開状態")
    is_deleted = models.BooleanField(default=False, verbose_name="削除フラグ")
    is_important = models.BooleanField(default=False, verbose_name="重要")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="作成者",
    )
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default="news", verbose_name="ジャンル"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        verbose_name = "お知らせ"

    def __str__(self):
        return self.title


# =========================
# カスタムユーザーマネージャ
# =========================
class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("The username must be set")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("rank", "visitor")
        return self._create_user(username, password, **extra_fields)

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("rank", "administer")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(username, password, **extra_fields)


# =========================
# ユーザー (User)
# =========================
class User(AbstractUser):
    RANK_CHOICES = [
        ("administer", "administer"),
        ("moderator", "moderator"),
        ("staff", "staff"),
        ("visitor", "visitor"),
    ]

    username = models.CharField(max_length=20, blank=False, null=False)
    rank = models.CharField(
        max_length=20, choices=RANK_CHOICES, default="visitor", verbose_name="ランク"
    )
    member_num = models.BigIntegerField(verbose_name="会員番号", default=random_num)
    email = models.EmailField(verbose_name="メールアドレス", unique=True)
    is_password_encrypted = models.BooleanField(
        default=False, verbose_name="パスワード暗号化フラグ"
    )
    avatar = models.ImageField(
        upload_to="avatars/", null=True, blank=True, verbose_name="プロフィール写真"
    )
    remarks = models.TextField(
        max_length=500, blank=True, verbose_name="備考・自己紹介"
    )

    # マイリスト: Mylistモデルを通じてCourseと多対多の関係
    # ※ Newsとの多対多はMylistモデル自体で管理するため、ここではCourse用として定義
    mylist = models.ManyToManyField(
        Course,
        through="Mylist",
        related_name="mylist_users",
        blank=True,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.username


# =========================
# 検定 (Exam)
# =========================
class Exam(models.Model):
    EXAM_TYPE_CHOICES = [
        ("mock", "仮試験"),
        ("main", "本試験"),
    ]

    title = models.CharField(verbose_name="検定名", max_length=200)
    exams_file = models.FileField(
        verbose_name="教材ファイル", upload_to="exams_files/", null=True, blank=True
    )
    description = models.TextField(verbose_name="説明・研修テキスト", blank=True)
    passing_score = models.IntegerField(verbose_name="合格基準点", default=80)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日")
    is_deleted = models.BooleanField(default=False, verbose_name="削除フラグ")
    is_active = models.BooleanField(default=True, verbose_name="公開状態")
    exam_type = models.CharField(
        max_length=10,
        choices=EXAM_TYPE_CHOICES,
        default="mock",
        verbose_name="試験タイプ",
    )

    # 前提となる仮試験 (本試験を受けるために合格が必要な試験)
    prerequisite = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="next_exams",
        verbose_name="前提となる仮試験",
    )
    time_limit = models.PositiveIntegerField(
        default=30,
        verbose_name="制限時間（分）",
        help_text="0を入力すると無制限になります",
    )

    def __str__(self):
        return f"[{self.get_exam_type_display()}] {self.title}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # 本試験が新規作成された場合、自動でバッジを作成
        if is_new and self.exam_type == "main":
            Badge.objects.create(exam=self, name=f"{self.title}")
        else:
            # 試験の公開状態に合わせてバッジの有効無効を同期
            if hasattr(self, "badge"):
                self.badge.is_active = self.is_active
                self.badge.save()


# =========================
# バッジ (Badge)
# =========================
class Badge(models.Model):
    exam = models.OneToOneField(Exam, on_delete=models.CASCADE, related_name="badge")
    name = models.CharField(verbose_name="バッジ名", max_length=100)
    icon = models.ImageField(
        verbose_name="バッジ画像", upload_to="badges/", null=True, blank=True
    )
    is_active = models.BooleanField(default=True, verbose_name="有効フラグ")

    def __str__(self):
        return self.name


# =========================
# 問題・選択肢 (Question / Choice)
# =========================
class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField(verbose_name="問題文")

    def __str__(self):
        return f"{self.exam.title} - {self.text[:20]}"


class Choice(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="choices"
    )
    text = models.CharField(verbose_name="選択肢の内容", max_length=200)
    is_correct = models.BooleanField(verbose_name="これが正解か", default=False)

    def __str__(self):
        return self.text


# =========================
# ユーザー検定合格状況 (Summary)
# =========================
class UserExamStatus(models.Model):
    """
    ユーザーの検定合格状況のサマリー（最新状態）
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="ユーザー"
    )
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, verbose_name="検定")
    is_passed = models.BooleanField(default=False, verbose_name="合格したか")
    passed_at = models.DateTimeField(null=True, blank=True, verbose_name="合格日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日")

    class Meta:
        unique_together = ("user", "exam")

    def __str__(self):
        return f"{self.user.username} - {self.exam.title} ({'合格' if self.is_passed else '未'})"


# =========================
# 【追加】ユーザー受験履歴 (Log)
# =========================
class ExamResult(models.Model):
    """
    ユーザーが試験を受けたごとの履歴（点数記録用）
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="受験者"
    )
    exam = models.ForeignKey(
        Exam, on_delete=models.CASCADE, verbose_name="受験した検定"
    )
    score = models.IntegerField(verbose_name="獲得スコア")
    is_passed = models.BooleanField(verbose_name="合否")
    taken_at = models.DateTimeField(auto_now_add=True, verbose_name="受験日時")

    def __str__(self):
        return f"{self.user.username} - {self.exam.title} - {self.score}点"


# =========================
# マイリスト (Mylist)
# =========================
class Mylist(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mylist_items"
    )
    # 講座をお気に入りする場合
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="mylists",  # related_nameを修正
        null=True,
        blank=True,
    )
    # お知らせをお気に入りする場合 (★追加)
    news = models.ForeignKey(
        News, on_delete=models.CASCADE, related_name="mylists", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="登録日時")

    class Meta:
        verbose_name = "マイリスト"
        constraints = [
            # UserとCourseの組み合わせはユニーク
            models.UniqueConstraint(
                fields=["user", "course"],
                name="unique_user_course_mylist",
                condition=models.Q(course__isnull=False),
            ),
            # UserとNewsの組み合わせはユニーク
            models.UniqueConstraint(
                fields=["user", "news"],
                name="unique_user_news_mylist",
                condition=models.Q(news__isnull=False),
            ),
        ]

    def clean(self):
        # CourseかNewsのどちらか一方は必須、かつ両方登録は不可（用途によるが今回は排他制御）
        if self.course is None and self.news is None:
            raise ValidationError("講座またはお知らせのいずれかを指定してください。")
        if self.course and self.news:
            raise ValidationError(
                "1つのマイリスト項目に講座とお知らせの両方を設定することはできません。"
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.course:
            return f"[Course] {self.user.username} - {self.course.subject}"
        elif self.news:
            return f"[News] {self.user.username} - {self.news.title}"
        return f"{self.user.username} - (Empty)"
