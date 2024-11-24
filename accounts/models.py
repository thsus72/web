from django.db import models

class User(models.Model):
    username = models.CharField(max_length=10, unique=True)
    password = models.CharField(max_length=128)  # 비밀번호는 해싱 예정
    email = models.EmailField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username
