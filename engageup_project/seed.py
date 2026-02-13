import os
import django
import random
from faker import Faker
from django.utils import timezone

# プロジェクト名に合わせる
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "engageup_project.settings")
django.setup()

from main.models import (
    User, Course, TrainingModule,
    TrainingExample, TrainingExampleChoice,
    News, Mylist,
    Exam, Question, Choice,
    UserExamStatus, ExamResult,
    UserModuleProgress
)

fake = Faker("ja_JP")


def run():

    print("=== ダミーデータ生成開始 ===")

    # -------------------------
    # Users
    # -------------------------
    users = []
    for _ in range(10):
        user = User.objects.create_user(
            email=fake.unique.email(),
            username=fake.user_name(),
            password="password",
            rank=random.choice(["visitor", "staff", "moderator"]),
            remarks=fake.text()
        )
        users.append(user)

    # -------------------------
    # Courses
    # -------------------------
    courses = []
    for _ in range(5):
        course = Course.objects.create(
            subject=fake.word(),
            courseCount=random.randint(1, 10),
        )
        courses.append(course)

    # -------------------------
    # Training Modules
    # -------------------------
    modules = []
    for course in courses:
        for i in range(3):
            module = TrainingModule.objects.create(
                course=course,
                title=fake.sentence(),
                content_text=fake.text(),
                estimated_time=random.randint(10, 120),
                order=i
            )
            modules.append(module)

    # -------------------------
    # Training Example + Choice
    # -------------------------
    for module in modules:
        for _ in range(2):
            example = TrainingExample.objects.create(
                module=module,
                text=fake.text(),
                explanation=fake.text()
            )

            correct_index = random.randint(0, 3)

            for i in range(4):
                TrainingExampleChoice.objects.create(
                    example=example,
                    text=fake.word(),
                    is_correct=(i == correct_index)
                )

    # -------------------------
    # News
    # -------------------------
    news_list = []
    for _ in range(5):
        news = News.objects.create(
            title=fake.sentence(),
            content=fake.text(),
            author=random.choice(users),
            category=random.choice(["news", "training", "urgent"]),
            is_important=random.choice([True, False])
        )
        news_list.append(news)

    # -------------------------
    # Exams
    # -------------------------
    exams = []
    for _ in range(3):
        exam = Exam.objects.create(
            title=fake.sentence(),
            description=fake.text(),
            passing_score=80,
            exam_type=random.choice(["mock", "main"]),
            time_limit=random.randint(20, 60)
        )
        exams.append(exam)

    # -------------------------
    # Questions + Choices
    # -------------------------
    for exam in exams:
        for _ in range(5):
            question = Question.objects.create(
                exam=exam,
                text=fake.text()
            )

            correct_index = random.randint(0, 3)

            for i in range(4):
                Choice.objects.create(
                    question=question,
                    text=fake.word(),
                    is_correct=(i == correct_index)
                )

    # -------------------------
    # Mylist（制約回避のためget_or_create使用）
    # -------------------------
    for user in users:
        for course in random.sample(courses, min(2, len(courses))):
            Mylist.objects.get_or_create(user=user, course=course)

        for news in random.sample(news_list, min(2, len(news_list))):
            Mylist.objects.get_or_create(user=user, news=news)

    # -------------------------
    # Exam Result + Status
    # -------------------------
    for user in users:
        for exam in exams:
            score = random.randint(50, 100)
            passed = score >= exam.passing_score

            ExamResult.objects.create(
                user=user,
                exam=exam,
                score=score,
                is_passed=passed
            )

            UserExamStatus.objects.update_or_create(
                user=user,
                exam=exam,
                defaults={
                    "is_passed": passed,
                    "passed_at": timezone.now() if passed else None
                }
            )

    # -------------------------
    # User Module Progress
    # -------------------------
    for user in users:
        for module in random.sample(modules, min(3, len(modules))):
            UserModuleProgress.objects.update_or_create(
                user=user,
                module=module,
                defaults={
                    "last_position": random.uniform(0, 300),
                    "is_completed": random.choice([True, False])
                }
            )

    print("=== ダミーデータ生成完了 ===")


if __name__ == "__main__":
    run()
