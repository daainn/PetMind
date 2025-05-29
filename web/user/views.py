from django.shortcuts import render, redirect
from django.contrib import messages
from .services.auth_service import authenticate_user
from .repositories.user_repository import user_exists_by_email, get_user_by_email
from .models import User
import uuid
from django.contrib.auth import authenticate, login
import random
import re
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings

def home(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = get_user_by_email(email)
        if not user:
            messages.error(request, '입력한 이메일 주소를 찾을 수 없습니다.')
        elif not check_password(password, user.password):
            messages.error(request, '비밀번호가 올바르지 않습니다.')
        else: 
            request.session.flush()
            request.session['user_id'] = str(user.id)
            request.session['user_email'] = user.email
            return redirect('chat:main')
    return render(request, 'user/home_01.html')

def chat_guest_view(request):
    request.session.flush()
    request.session['guest'] = True

    guest_email = f"guest_{uuid.uuid4().hex[:10]}@example.com"
    guest_user = User.objects.create(email=guest_email, password='guest_pw')
    request.session['guest_user_id'] = str(guest_user.id)
    request.session['user_email'] = guest_email
    return redirect('chat:main')

def logout_view(request):
    request.session.flush()
    messages.info(request, "로그아웃 되었습니다.")
    return redirect('user:home')

def find_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if user_exists_by_email(email):
            request.session['reset_email'] = email
            return redirect('user:find_password_complete')
        else:
            messages.error(request, '입력한 이메일 주소를 찾을 수 없습니다.')
    return render(request, 'user/search_01.html')

def find_password_complete(request):
    email = request.session.get('reset_email')
    user = get_user_by_email(email)
    return render(request, 'user/search_02.html', {'user': user})

def info(request):
    if request.method == 'POST':
        return redirect('user:info')
    return render(request, 'dogs/info.html')

def get_or_create_user(request):
    if request.user.is_authenticated:
        return request.user, True
    temp_email = f"guest_{uuid.uuid4().hex[:10]}@example.com"
    user = User.objects.create(email=temp_email, password="guest_password")
    return user, False


def info_cancel(request):
    messages.info(request, "입력이 취소되었습니다.")
    return redirect("user:home")

def join_user_form(request):
    return render(request, 'user/join_01.html')

def join_user_email_form(request):
    if request.method == 'POST':
        email_id = request.POST.get('email_id')
        email_domain = request.POST.get('email_domain')
        password = request.POST.get('password')
        full_email = f"{email_id}@{email_domain}"

        try:
            validate_email(full_email)
        except ValidationError:
            messages.error(request, '유효하지 않은 이메일 형식입니다.')
            return redirect('user:join_01')

        if User.objects.filter(email=full_email).exists():
            messages.error(request, '이미 등록된 이메일입니다.')
            return redirect('user:join_01')

        if not re.match(r'^(?=.*[A-Za-z])(?=.*\d|[^A-Za-z\d])(?=.{8,16}).*$', password):
            messages.error(request, '비밀번호 형식이 올바르지 않습니다.')
            return redirect('user:join_01')

        auth_code = str(random.randint(10000, 99999))
        request.session['user_email'] = full_email
        request.session['user_password'] = password
        request.session['auth_code'] = auth_code

        subject = "[PetMind] 이메일 인증번호 안내"
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [full_email]
        verification_link = "http://localhost:8080/join/email/certification"

        html_content = render_to_string('email_verification.html', {
            'verification_code': auth_code,
            'verification_link': verification_link
        })

        email = EmailMultiAlternatives(subject, '', from_email, to_email)
        email.attach_alternative(html_content, "text/html")
        email.send()

        return redirect('user:join_03')

    return redirect('user:join_01')

def join_user_email_certification(request):
    if request.method == 'POST':
        user_input = request.POST.get('auth_code')
        session_code = request.session.get('auth_code')
        email = request.session.get('user_email')
        password = request.session.get('user_password')

        if not email or not password or not session_code:
            messages.error(request, '세션이 만료되었습니다. 다시 회원가입을 진행해주세요.')
            return redirect('user:join_01')

        if user_input != session_code:
            return render(request, 'user/join_03.html', {
                'error': '❌ 인증번호가 일치하지 않습니다. 다시 입력해주세요.'
            })

        try:
            validate_email(email)
        except ValidationError:
            return render(request, 'user/join_03.html', {
                'error': '❌ 유효하지 않은 이메일 형식입니다.'
            })

        if User.objects.filter(email=email).exists():
            return render(request, 'user/join_03.html', {
                'error': '❌ 이미 등록된 이메일입니다. 로그인 또는 비밀번호 찾기를 이용해주세요.'
            })

        if not re.match(r'^(?=.*[A-Za-z])(?=.*\d|[^A-Za-z\d])(?=.{8,16}).*$', password):
            return render(request, 'user/join_03.html', {
                'error': '❌ 비밀번호는 영문자와 숫자 또는 특수문자를 포함한 8~16자여야 합니다.'
            })

        try:
            hashed_pw = make_password(password)
            user = User(email=email, password=hashed_pw, is_verified=True)
            user.save()
        except Exception as e:
            return render(request, 'user/join_03.html', {
                'error': f'❌ 회원가입에 실패했습니다. 관리자에게 문의해주세요. ({str(e)})'
            })

        response = redirect('user:join_04')
        request.session.flush()
        return response

    return render(request, 'user/join_03.html', {
        'error': '❗ 인증 절차를 완료하려면 인증번호를 입력해주세요.'
    })

def join_terms_privacy(request):
    return render(request, 'user/join_p_terms_privacy.html')

def join_terms_service(request):
    return render(request, 'user/join_p_terms_service.html')

def join_user_complete(request):
    return render(request, 'user/join_04.html')
