# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
import random


def random_num():  # 会員の番号を作成する　同じ番号が出現する可能性は考慮しない
    return random.randint(1000000000000, 10000000000000)


class Constant(models.Model):  # 定数をまとめたテーブル
    company_code = models.CharField(
        verbose_name="会社コード", max_length=20, default="com"
    )
    address = models.CharField(
        verbose_name="アドレス", max_length=20, default="gmail.com"
    )

    def __str__(self):
        return self.company_code


class Course(models.Model):  # 講座
    subject = models.CharField(verbose_name="科目", max_length=50)  # 科目
    courseCount = models.IntegerField(verbose_name="講座数")  # 講座数
    is_mylist = models.BooleanField(
        verbose_name="マイリストに入っているか", default=False
    )  # マイリストに入っているか

    is_active = models.BooleanField(default=True)  # アクティブかどうかを調べる


from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


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


class User(AbstractUser):  # ユーザーのランク
    RANK_CHOICES = [
        ("administer", "administer"),
        ("moderator", "moderator"),
        ("staff", "staff"),
        ("visitor", "visitor"),
    ]

    rank = models.CharField(  # ユーザーのランクを選ぶ
        max_length=20, choices=RANK_CHOICES, default="visitor", verbose_name="ランク"
    )

    member_num = models.BigIntegerField(  # 会員の番号を持つ
        verbose_name="会員番号", primary_key=True, default=random_num
    )

    name = models.CharField(verbose_name="氏名", max_length=20)  # 名前を持つ
    email = models.EmailField(
        verbose_name="メールアドレス", unique=True
    )  # メールアドレスを持つ
    is_password_encrypted = models.BooleanField(
        default=False, verbose_name="パスワード暗号化フラグ"
    )  # パスワードを暗号化　削除するか検討

    #  追加：プロフィール写真
    avatar = models.ImageField(
        upload_to="avatars/", 
        null=True, 
        blank=True, 
        verbose_name="プロフィール写真"
    )
    #  追加：備考欄（自己紹介）
    remarks = models.TextField(
        max_length=500, 
        blank=True, 
        verbose_name="備考・自己紹介"
    )

    USERNAME_FIELD = "email"  # ユーザーネームを打ち込む
    REQUIRED_FIELDS = ["username"]
    username = models.CharField(
        max_length=20, blank=False, null=False
    )  # ユーザーネームを打ち込む

    objects = UserManager()

    def __str__(self):
        return self.username

class Badge(models.Model):  # バッジ
    exam = models.OneToOneField("Exam", on_delete=models.CASCADE, related_name="badge")
    name = models.CharField(verbose_name="バッジ名", max_length=100)
    icon = models.ImageField(
        verbose_name="バッジ画像", upload_to="badges/", null=True, blank=True
    )
    is_active = models.BooleanField(default=True, verbose_name="有効フラグ")

    def __str__(self):
        return self.name

class Exam(models.Model):  # 検定
    # --- 試験タイプ（仮・本）の選択肢 ---
    EXAM_TYPE_CHOICES = [
        ('mock', '仮試験'),
        ('main', '本試験'),
    ]
    title = models.CharField(verbose_name="検定名", max_length=100)
    exams_file = models.FileField(verbose_name="教材ファイル", upload_to="exams_files/", null=True, blank=True)
    description = models.TextField(verbose_name="説明・研修テキスト", blank=True) 
    passing_score = models.IntegerField(verbose_name="合格基準点", default=80) # 自動採点に必要
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日") # 管理用
    is_active = models.BooleanField(default=True, verbose_name="有効フラグ") # 検定が有効かどうか
    
    # ★追加：仮試験か本試験か
    exam_type = models.CharField(max_length=10, choices=EXAM_TYPE_CHOICES, default='mock', verbose_name="試験タイプ")
    
    # ★追加：本試験の場合の前提条件（どの仮試験をクリアすべきか）
    prerequisite = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, 
        verbose_name="前提となる仮試験", related_name="next_exams"
    )

    def __str__(self):
        return f"[{self.get_exam_type_display()}] {self.title}"

    
    

    def save(self, *args, **kwargs):
        # 新規作成かどうかの判定
        is_new = self.pk is None
        # まずは検定自体を保存
        super().save(*args, **kwargs)

        if is_new and self.exam_type == 'main':
            # Badgeクラスはこの下にありますが、メソッドの中なので呼び出せます
            Badge.objects.create(exam=self, name=f"{self.title}合格バッジ")
        else:
            # 既存の検定が更新された場合、関連するバッジも更新
            if hasattr(self, 'badge'):
                self.badge.is_active = self.is_active
                self.badge.save()



class Question(models.Model):
    # どの検定の問題か
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField(verbose_name="問題文")

    def __str__(self):
        return f"{self.exam.title} - {self.text[:20]}"

class Choice(models.Model):
    # どの問題の選択肢か
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(verbose_name="選択肢の内容", max_length=200)
    is_correct = models.BooleanField(verbose_name="これが正解か", default=False)

    def __str__(self):
        return self.text



class News(models.Model):
    title = models.CharField(verbose_name="お知らせ名",max_length=100)
    content = models.TextField(verbose_name="内容")
    is_active = models.BooleanField(default=True)  # アクティブかどうかを調べる
    

# ★新規追加：ユーザーがどの試験に合格したかを記録する
class UserExamStatus(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, verbose_name="ユーザー")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, verbose_name="検定")
    is_passed = models.BooleanField(default=False, verbose_name="合格したか")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日")

    class Meta:
        unique_together = ('user', 'exam') # 1人1試験1レコード

    def __str__(self):
        return f"{self.user.username} - {self.exam.title} ({'合格' if self.is_passed else '未'})"
    
