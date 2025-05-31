from django.shortcuts import render, redirect
from django.contrib import messages
from .services.auth_service import authenticate_user
from .repositories.user_repository import user_exists_by_email, get_user_by_email
from .models import User
from dogs.models import DogProfile
from django.urls import reverse
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
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

def home(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = get_user_by_email(email)
        if not user:
            messages.error(request, '입력한 이메일 주소를 찾을 수 없습니다.')
        else:
            # ✅ 디버깅 로그
            print(f"[DEBUG] 입력된 비밀번호: {password}")
            print(f"[DEBUG] DB 비밀번호 해시: {user.password}")
            print(f"[DEBUG] check_password 결과: {check_password(password, user.password)}")

            if not check_password(password, user.password):
                messages.error(request, '비밀번호가 올바르지 않습니다.')
            else:
                request.session.flush()
                request.session['user_id'] = str(user.id)
                request.session['user_email'] = user.email

                dogs = DogProfile.objects.filter(user=user.id).order_by('-created_at')

                if not dogs.exists():
                    return redirect('dogs:dog_info_join')
                else:
                    latest_dog = dogs.first()
                    return redirect('chat:main', dog_id=latest_dog.dog_id)

    return render(request, 'user/home_01.html')

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
        return redirect('dogs:dog_info_join')
    return render(request, 'dogs/dog_info_join.html')

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
    return redirect('user:join_01')

def join_user_email_certification(request):
    return render(request, 'user/join_03.html', {
        'error': '❗ 인증 절차를 완료하려면 인증번호를 입력해주세요.'
    })

def join_terms_privacy(request):
    return render(request, 'user/join_p_terms_privacy.html')

def join_terms_service(request):
    return render(request, 'user/join_p_terms_service.html')


def join_user_complete(request):
    if request.method == 'POST':
        email_id = request.POST.get('email_id')
        email_domain = request.POST.get('email_domain')
        password = request.POST.get('password')

        email = f"{email_id}@{email_domain}"
        print(f"[DEBUG] 가입 이메일: {email}")
        print(f"[DEBUG] 가입 원문 비밀번호: {password}")

        if not password:
            messages.error(request, "비밀번호가 누락되었습니다.")
            return redirect('user:join_01')

        if not User.objects.filter(email=email).exists():
            hashed = make_password(password)
            print(f"[DEBUG] 해시된 비밀번호: {hashed}")
            user = User.objects.create(
                email=email,
                password=hashed,
                is_verified=True
            )
        else:
            user = User.objects.get(email=email)

        request.session['user_email'] = email
        return render(request, 'user/home_01.html')

    return redirect('user:join_01')




@csrf_exempt 
def send_auth_code(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            if not email:
                return JsonResponse({'success': False, 'message': '이메일이 없습니다.'}, status=400)

            auth_code = str(random.randint(10000, 99999))
            request.session['auth_code'] = auth_code
            request.session['user_email'] = email

            subject = "[PetMind] 이메일 인증번호 안내"
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [email]

            html_content = render_to_string('email_verification.html', {
                'verification_code': auth_code
            })

            email_message = EmailMultiAlternatives(subject, '', from_email, to_email)
            email_message.attach_alternative(html_content, "text/html")
            email_message.send()

            return JsonResponse({'success': True})
        except Exception as e:
            print(f"[ERROR] {e}")
            return JsonResponse({'success': False, 'message': '서버 오류'}, status=500)

    return JsonResponse({'success': False, 'message': '잘못된 요청'}, status=405)

@csrf_exempt
def verify_auth_code(request):
    if request.method == 'POST':
        import json
        body = json.loads(request.body)
        email = body.get('email')
        code = body.get('code')
        session_code = request.session.get('auth_code')
        session_email = request.session.get('user_email')

        if not session_code or not session_email:
            return JsonResponse({'success': False, 'message': '세션이 만료되었습니다.'})

        if email != session_email:
            return JsonResponse({'success': False, 'message': '이메일이 일치하지 않습니다.'})

        if code != session_code:
            return JsonResponse({'success': False, 'message': '인증번호가 일치하지 않습니다.'})

        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})