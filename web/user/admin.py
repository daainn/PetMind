import re
from django.contrib import admin
from django import forms
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from .models import User

# 사용자 정의 회원가입 폼
class UserCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'password']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        username = email.split('@')[0]

        if not re.match(r'^[a-z0-9]{5,20}$', username):
            raise ValidationError("아이디는 영문 소문자, 숫자를 혼용하여 5~20자 입력해주세요.")

        if User.objects.filter(email=email).exists():
            raise ValidationError("이미 등록된 이메일입니다.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')

        if len(password) < 8 or len(password) > 16:
            raise ValidationError("비밀번호는 8~16자 입력해주세요.")

        # 조건: 대소문자, 숫자, 특수문자 중 2종 이상
        conditions = [
            bool(re.search(r'[A-Z]', password)),      # 대문자
            bool(re.search(r'[a-z]', password)),      # 소문자
            bool(re.search(r'[0-9]', password)),      # 숫자
            bool(re.search(r'[^A-Za-z0-9]', password))  # 특수문자
        ]

        if sum(conditions) < 2:
            raise ValidationError("비밀번호는 영문 대/소문자, 숫자, 특수문자 중 2종류 이상을 혼합해야 합니다.")

        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.password = make_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_verified', 'created_at']
    search_fields = ['email']
    ordering = ['-created_at']

