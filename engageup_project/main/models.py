# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
import random

def random_num():           #会員の番号を作成する　同じ番号が出現する可能性は考慮しない
    return random.randint(1000000000000, 10000000000000)
class Constant(models.Model):    #定数をまとめたテーブル
    company_code = models.CharField(verbose_name="会社コード",max_length=20,default="com")
    address = models.CharField(verbose_name="アドレス",max_length=20,default="gmail.com")
    def __str__(self):
        return self.company_code


class Course(models.Model): #講座
    subject = models.CharField(verbose_name="科目", max_length=50)  #科目
    course_count = models.IntegerField(verbose_name="講座数")    #講座数
    is_mylist = models.BooleanField(verbose_name="マイリストに入っているか",default=False)  #マイリストに入っているか



from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The username must be set')

        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('rank', 'visitor')

        return self._create_user(username, password, **extra_fields)

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('rank', 'administer')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, password, **extra_fields)


class User(AbstractUser):   #ユーザーのランク
    RANK_CHOICES = [
        ("administer","管理者"),
        ("moderator","モデレーター"),
        ("staff","社員"),
        ("visitor","訪問者"),
    ]

    rank = models.CharField(    #ユーザーのランクを選ぶ
        max_length=20,
        choices=RANK_CHOICES,
        default="visitor",
        verbose_name="ランク"
    )

    member_num = models.BigIntegerField(    #会員の番号を持つ
        verbose_name="会員番号",
        primary_key=True,
        default=random_num
    )

    name = models.CharField(verbose_name="氏名", max_length=20) #名前を持つ
    email = models.EmailField(verbose_name="メールアドレス", unique=True)   #メールアドレスを持つ
    is_password_encrypted = models.BooleanField(default=False, verbose_name="パスワード暗号化フラグ")   #パスワードを暗号化　削除するか検討

    USERNAME_FIELD = 'email'    #ユーザーネームを打ち込む
    REQUIRED_FIELDS = ['username']
    username = models.CharField(max_length=20, blank=False, null=False)   #ユーザーネームを打ち込む

    objects = UserManager()

    def __str__(self):
        return self.username


