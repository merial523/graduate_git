# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
import random

def random_num():           #会員の番号を作成する　同じ番号が出現する可能性は考慮しない
    return random.randint(1000000000000, 10000000000000)

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

class Course(): #講座
    subject = models.CharField(verbose_name="科目", max_length=50)  #科目
    courseCount = models.IntegerField(verbose_name="講座数")    #講座数
    is_mylist = models.BooleanField(verbose_name="マイリストに入っているか",default=False)  #マイリストに入っているか