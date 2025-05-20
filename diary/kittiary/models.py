from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    GENDER_CHOICES = [('M', '남성'), ('F', '여성')]
    
    social_login_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    is_profile_completed = models.BooleanField(default=False)

    # Fix for reverse accessor clashes
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='kittiary_users',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='kittiary_users',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    class Meta:
        db_table = 'user'

class Family(models.Model):
    RELATIONSHIP_CHOICES = [
        ('SPOUSE', '배우자'),
        ('CHILD', '자녀'),
        ('SIBLING', '형제자매'),
        ('PARENT', '부모님'),
        ('GRANDPARENT', '조부모'),
        ('OTHER', '기타'),
        ('NONE', '가족이 없습니다/가입하고 싶지 않습니다')
    ]
    GENDER_CHOICES = [('M', '남성'), ('F', '여성')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='families')
    name = models.CharField(max_length=100, null=True, blank=True)
    relationship = models.CharField(max_length=50, choices=RELATIONSHIP_CHOICES)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True)

    class Meta:
        db_table = 'family'

class Diary(models.Model):
    CATEGORY_CHOICES = [
        ('DAILY', 'Daily'),
        ('TOPIC', 'Topic'),
        ('REMINISCENCE', 'Reminiscence'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diaries')
    diary_date = models.DateField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'diary'

class QnA(models.Model):
    diary = models.ForeignKey(Diary, on_delete=models.CASCADE, related_name='qnas')
    question = models.TextField(help_text="회상 질문")
    correct_answer = models.TextField(help_text="정답")
    user_response = models.TextField(help_text="사용자 답변")
    correctness = models.FloatField(
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="답변의 정확도 (0-100)"
    )
    response_time = models.IntegerField(
        null=True,
        help_text="답변 시간 (초)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'qna'
        verbose_name = 'QnA'
        verbose_name_plural = 'QnAs'

    def __str__(self):
        return f"Q: {self.question[:30]}... - {self.diary.diary_date}"

class Stats(models.Model):
    CATEGORY_CHOICES = [
        ('TIME_ORIENTATION', '시간지남'),
        ('PLACE_ORIENTATION', '장소지남'),
        ('MEMORY', '기억'),
        ('LANGUAGE_CALC', '언어/계산'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stats')
    stat_date = models.DateField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    accuracy = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    response_time = models.IntegerField()  # in seconds
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stats'
