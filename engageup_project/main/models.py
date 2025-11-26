# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
import random

def random_num():
    return random.randint(1000000000000, 10000000000000)

class User(AbstractUser):
    RANK_CHOICES = [
        ("administer","管理者"),
        ("moderator","モデレーター"),
        ("staff","社員"),
        ("visitor","訪問者"),
    ]

    rank = models.CharField(
        max_length=20,
        choices=RANK_CHOICES,
        default="visitor",
        verbose_name="ランク"
    )

    member_num = models.BigIntegerField(
        verbose_name="会員番号",
        primary_key=True,
        default=random_num
    )

    name = models.CharField(verbose_name="氏名", max_length=20)
    email = models.EmailField(verbose_name="メールアドレス", unique=True)
    is_password_encrypted = models.BooleanField(default=False, verbose_name="パスワード暗号化フラグ")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    username = models.CharField(max_length=20, blank=True, null=True)

class Course():
    subject = models.CharField(verbose_name="科目", max_length=50)
    courseCount = models.IntegerField(verbose_name="講座数")
    is_mylist = models.BooleanField(verbose_name="マイリストに入っているか",default=False)
