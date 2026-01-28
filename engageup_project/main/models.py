# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import random


def random_num():
    """
    会員番号を生成
    ※ 同じ番号が出現する可能性は考慮しない
    """
    return random.randint(1000000000000, 10000000000000)


# =========================
# 定数テーブル
# =========================
class Constant(models.Model):
    company_code = models.CharField(
        verbose_name="会社コード",
        max_length=20,
        default="com"
    )
    address = models.CharField(
        verbose_name="アドレス",
        max_length=20,
        default="gmail.com"
    )

    def __str__(self):
        return self.company_code


# =========================
# 講座
# =========================
class Course(models.Model):
    subject = models.CharField(
        verbose_name="講座名",
        max_length=50
    )
    courseCount = models.IntegerField(
        verbose_name="講座数"
    )
    is_mylist = models.BooleanField(
        verbose_name="マイリストに入っているか",
        default=False
    )
    is_active = models.BooleanField(
        verbose_name = "有効かどうか",
        default=True
    )

    def __str__(self):
        return self.subject


# =========================
# 研修モジュール（コース内）
# =========================
class TrainingModule(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="modules",
        verbose_name="所属コース"
    )
    title = models.CharField(
        verbose_name="研修名",
        max_length=100
    )

    video = models.FileField(
        verbose_name="研修動画",
        upload_to="training_videos/",
        null=True,
        blank=True
    )

    training_file = models.FileField(
        verbose_name="要約元資料(PDF/画像)",
        upload_to="exams_files/",
        null=True,
        blank=True
    )

    estimated_time = models.PositiveIntegerField(
        verbose_name="推奨学習時間(分)",
        default=30,
        help_text="受講者がこの研修を終えるのにかかる目安の時間（分）です"
    )

    content_text = models.TextField(
        verbose_name="研修テキスト",
        blank=True
    )

    order = models.IntegerField(
        verbose_name="表示順",
        default=0
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="有効フラグ"
    )

    def __str__(self):
        return f"{self.course.subject} - {self.title}"


# =========================
# 研修内の例題
# =========================
class TrainingExample(models.Model):
    module = models.ForeignKey(
        TrainingModule,
        on_delete=models.CASCADE,
        related_name="examples",
        verbose_name="対象研修"
    )
    text = models.TextField(
        verbose_name="例題文"
    )
    explanation = models.TextField(
        verbose_name="解説",
        blank=True
    )

    def __str__(self):
        return f"例題: {self.text[:20]}"


class TrainingExampleChoice(models.Model):
    example = models.ForeignKey(
        TrainingExample,
        on_delete=models.CASCADE,
        related_name="choices"
    )
    text = models.CharField(
        verbose_name="選択肢",
        max_length=200
    )
    is_correct = models.BooleanField(
        verbose_name="これが正解か",
        default=False
    )

    def __str__(self):
        return self.text


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
# ユーザー
# =========================
class User(AbstractUser):       #名前、ランク、会員番号、メールアドレス、プロフ写真、備考

    username = models.CharField(
        max_length=20,
        blank=False,
        null=False
    )
    RANK_CHOICES = [
        ("administer", "administer"),
        ("moderator", "moderator"),
        ("staff", "staff"),
        ("visitor", "visitor"),
    ]

    rank = models.CharField(
        max_length=20,
        choices=RANK_CHOICES,
        default="visitor",
        verbose_name="ランク"
    )

    member_num = models.BigIntegerField(
        verbose_name="会員番号",
        default=random_num
    )


    email = models.EmailField(
        verbose_name="メールアドレス",
        unique=True
    )

    is_password_encrypted = models.BooleanField(
        default=False,
        verbose_name="パスワード暗号化フラグ"
    )

    avatar = models.ImageField(
        upload_to="avatars/",
        null=True,
        blank=True,
        verbose_name="プロフィール写真"
    )

    remarks = models.TextField(
        max_length=500,
        blank=True,
        verbose_name="備考・自己紹介"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]



    objects = UserManager()

    def __str__(self):
        return self.username


# =========================
# バッジ
# =========================
class Badge(models.Model):
    exam = models.OneToOneField(
        "Exam",
        on_delete=models.CASCADE,
        related_name="badge"
    )
    name = models.CharField(
        verbose_name="バッジ名",
        max_length=100
    )
    icon = models.ImageField(
        verbose_name="バッジ画像",
        upload_to="badges/",
        null=True,
        blank=True
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="有効フラグ"
    )

    def __str__(self):
        return self.name


# =========================
# 検定
# =========================
class Exam(models.Model):
    EXAM_TYPE_CHOICES = [
        ("mock", "仮試験"),
        ("main", "本試験"),
    ]

    title = models.CharField(
        verbose_name="検定名",
        max_length=100
    )
    exams_file = models.FileField(
        verbose_name="教材ファイル",
        upload_to="exams_files/",
        null=True,
        blank=True
    )
    description = models.TextField(
        verbose_name="説明・研修テキスト",
        blank=True
    )
    passing_score = models.IntegerField(
        verbose_name="合格基準点",
        default=80
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="作成日"
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name="削除フラグ"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="公開状態"
    )
    exam_type = models.CharField(
        max_length=10,
        choices=EXAM_TYPE_CHOICES,
        default="mock",
        verbose_name="試験タイプ"
    )
    prerequisite = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="next_exams",
        verbose_name="前提となる仮試験"
    )

    def __str__(self):
        return f"[{self.get_exam_type_display()}] {self.title}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and self.exam_type == "main":
            Badge.objects.create(
                exam=self,
                name=f"{self.title}合格バッジ"
            )
        else:
            if hasattr(self, "badge"):
                self.badge.is_active = self.is_active
                self.badge.save()


# =========================
# 問題・選択肢
# =========================
class Question(models.Model):
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="questions"
    )
    text = models.TextField(
        verbose_name="問題文"
    )

    def __str__(self):
        return f"{self.exam.title} - {self.text[:20]}"


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices"
    )
    text = models.CharField(
        verbose_name="選択肢の内容",
        max_length=200
    )
    is_correct = models.BooleanField(
        verbose_name="これが正解か",
        default=False
    )

    def __str__(self):
        return self.text


# =========================
# お知らせ
# =========================
class News(models.Model):
    title = models.CharField(
        verbose_name="お知らせ名",
        max_length=100
    )
    content = models.TextField(
        verbose_name="内容"
    )
    is_active = models.BooleanField(
        default=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="投稿日"
    )


# =========================
# ユーザー検定合格状況
# =========================
class UserExamStatus(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="ユーザー"
        )
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        verbose_name="検定"
    )
    is_passed = models.BooleanField(
        default=False,
        verbose_name="合格したか"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新日"
    )

    class Meta:
        unique_together = ("user", "exam")

    def __str__(self):
        return f"{self.user.username} - {self.exam.title} ({'合格' if self.is_passed else '未'})"
