from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .services.auth_service import authenticate_user
from .repositories.user_repository import user_exists_by_email, get_user_by_email
from .models import User
from chat.models import Chat, UserReview
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
from django.views.decorators.http import require_POST
import json
from django.utils.crypto import get_random_string

def home(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = get_user_by_email(email)

        if not user:
            messages.error(request, '입력한 이메일 주소를 찾을 수 없습니다.')
        elif not check_password(password, user.password):
            print(f"[DEBUG] 입력된 비밀번호: {password}")
            print(f"[DEBUG] 저장된 해시 비밀번호: {user.password}")
            messages.error(request, '비밀번호가 올바르지 않습니다.')
        else:
            request.session.flush()
            request.session['user_id'] = str(user.id)
            request.session['user_email'] = user.email

            dogs = DogProfile.objects.filter(user=user).order_by('-created_at')
            if dogs.exists():
                latest_dog = dogs.first()
                request.session['current_dog_id'] = latest_dog.id
                return redirect('chat:chat_member', dog_id=latest_dog.id)
            else:
                return redirect('dogs:dog_info_join')

    return render(request, 'user/home_01.html')

            
            
def logout_view(request):
    request.session.flush()
    messages.info(request, "로그아웃 되었습니다.")
    return redirect('user:home')

def find_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = get_user_by_email(email)

        if user:
            try:
                temp_password = get_random_string(length=10)
                user.password = make_password(temp_password)
                user.save()

                subject = "[PetMind] 임시 비밀번호 안내"
                from_email = settings.DEFAULT_FROM_EMAIL
                to_email = [email]

                html_content = render_to_string('email_temp_password.html', {
                    'temp_password': temp_password,
                    'user': user,
                })

                email_message = EmailMultiAlternatives(subject, '', from_email, to_email)
                email_message.attach_alternative(html_content, "text/html")
                email_message.send()

                return render(request, 'user/search_01.html', {
                    'email_sent': True
                })

            except Exception as e:
                messages.error(request, '이메일 발송 중 문제가 발생했습니다. 다시 시도해주세요.')
                return redirect('user:find_password')
        else:
            messages.error(request, '입력한 이메일 주소를 찾을 수 없습니다.')

    return render(request, 'user/search_01.html')


def info(request):
    if request.method == 'POST':
        return redirect('dogs:dog_info_join')
    return render(request, 'dogs/dog_info_join.html')

def get_or_create_user(request):
    user_id = request.session.get('user_id')
    if user_id:
        try:
            user = User.objects.get(id=user_id)
            return user, True
        except User.DoesNotExist:
            pass

    temp_email = f"guest_{uuid.uuid4().hex[:10]}@example.com"
    user = User.objects.create(email=temp_email, password="guest_password")
    request.session['guest'] = True
    request.session['guest_user_id'] = str(user.id)
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

@require_POST
def update_info(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})

    current_password = request.POST.get('current_password')
    new_password = request.POST.get('new_password')

    if not check_password(current_password, user.password):
        return JsonResponse({'success': False, 'message': '기존 비밀번호가 올바르지 않습니다.'})

    user.password = make_password(new_password)
    user.save()

    return JsonResponse({'success': True, 'message': '비밀번호가 성공적으로 변경되었습니다.'})

def user_feedback(request):
    return render(request, 'user/user_feedback.html')


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

        request.session.flush()
        request.session['user_id'] = str(user.id)
        request.session['user_email'] = user.email
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


@require_POST
def withdraw_user(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('user:home')

    try:
        user = User.objects.get(id=user_id)
        user.delete()
        request.session.flush()
    except User.DoesNotExist:
        pass

    return redirect('user:home')

@require_POST
def submit_feedback(request):
    chat_id = request.POST.get('chat_id')
    rating = request.POST.get('rating')
    text = request.POST.get('text')

    if not rating or not chat_id:
        return JsonResponse({'status': 'error', 'message': '누락된 정보가 있습니다.'}, status=400)

    try:
        chat_id = int(chat_id)
    except (TypeError, ValueError):
        return JsonResponse({'status': 'error', 'message': '유효하지 않은 chat_id입니다.'}, status=400)

    if UserReview.objects.filter(chat_id=chat_id).exists():
        return JsonResponse({'status': 'duplicate'})

    try:
        UserReview.objects.create(
            chat_id=chat_id,
            review_score=int(rating),
            review=text
        )
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)