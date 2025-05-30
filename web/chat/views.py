from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from user.models import User
from .models import Chat, Message
from dogs.models import DogProfile
import uuid
import requests

# 공통 진입점 (회원/비회원 분기)
def chat_entry(request):
    if request.session.get('guest'):
        return redirect('chat:main')
    elif request.session.get('user_id'):
        return redirect('chat:main')
    else:
        return redirect('user:home')

# 메인 채팅 페이지
def chat_main(request):
    is_guest = request.session.get("guest", False)
    user_id = request.session.get("user_id")
    guest_user_id = request.session.get("guest_user_id")
    user_email = request.session.get("user_email")
    current_dog_id = request.session.get("current_dog_id")

    chat_list, current_chat, messages = [], None, []

    if user_id and not is_guest:
        try:
            user = User.objects.get(id=user_id)
            # ✅ 회원의 반려견 채팅 리스트
            chat_list = Chat.objects.filter(dog__user=user).order_by('-created_at')

            if current_dog_id:
                current_chat = Chat.objects.filter(dog__id=current_dog_id).first()
            else:
                # 세션에 current_dog_id 없으면 첫 채팅의 반려견 ID를 저장
                current_chat = chat_list.first()
                if current_chat and current_chat.dog:
                    request.session["current_dog_id"] = current_chat.dog.id

        except User.DoesNotExist:
            return redirect('user:home')

    elif is_guest and guest_user_id:
        try:
            user = User.objects.get(id=guest_user_id)
            # ✅ 비회원 채팅 리스트 (dog=None and user=guest)
            chat_list = Chat.objects.filter(dog=None, user=user).order_by('-created_at')
            current_chat = chat_list.first()
        except User.DoesNotExist:
            return redirect('chat:chat_guest_view')

    else:
        return redirect('user:home')

    if current_chat:
        messages = Message.objects.filter(chat=current_chat).order_by('created_at')

    return render(request, 'chat/chat.html', {
        'chat_list': chat_list,
        'current_chat': current_chat,
        'chat_messages': messages,
        'is_guest': is_guest,
        'user_email': user_email,
    })


# 채팅 제목 클릭 시 해당 채팅으로 이동
@require_POST
def chat_member_start(request, chat_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('user:home')

    try:
        user = User.objects.get(id=user_id)
        chat = Chat.objects.get(id=chat_id, dog__user=user)
    except (User.DoesNotExist, Chat.DoesNotExist):
        return redirect('chat:main')

    chat_list = Chat.objects.filter(dog__user=user).order_by('-created_at')
    messages = Message.objects.filter(chat=chat).order_by('created_at')
    user_email = request.session.get('user_email')

    return render(request, 'chat/chat.html', {
        'chat_list': chat_list,
        'current_chat': chat,
        'chat_messages': messages,
        'user_email': user_email,
        'is_guest': False,
    })


def call_runpod_api(message, user_info):
    try:
        api_url = "https://x76r8kryd0u399-7004.proxy.runpod.net/chat"
        payload = {
            "message": message,
            "user_info": user_info
        }
        res = requests.post(api_url, json=payload, timeout=120)
        res.raise_for_status()
        data = res.json()
        return data.get("response", "⚠️ 응답이 없습니다.")
    except Exception as e:
        return f"❗ 오류 발생: {str(e)}"
    
def select_dog(request, dog_id):
    if not request.session.get("user_id"):
        return redirect("user:home")
    request.session['current_dog_id'] = dog_id
    return redirect('chat:main')
    
def get_dog_info(dog):
    return {
        "name": dog.name,
        "breed": dog.breed_name,
        "age": dog.age,
        "gender": dog.gender,
        "neutered": dog.neutered,
        "disease": "있음" if dog.disease_history else "없음",
        "disease_desc": dog.disease_history or "",
        "period": dog.living_period,
        "housing": dog.housing_type,
        "chat_history": [],
        "prev_q": None,
        "prev_a": None,
        "prev_cate": None,
        "is_first_question": True
    }

def get_minimal_guest_info(session):
    breed = session.get("guest_dog_breed", "견종 정보 없음")
    return {
        "name": "비회원견",
        "breed": breed,
        "chat_history": [],
        "prev_q": None,
        "prev_a": None,
        "prev_cate": None,
        "is_first_question": True
    }

def get_chat_history(chat):
    past_msgs = Message.objects.filter(chat=chat).order_by("created_at")
    chat_history = [{"role": m.sender, "content": m.message} for m in past_msgs]

    prev_q, prev_a = None, None
    for i in range(len(chat_history) - 2, -1, -2):
        if chat_history[i]["role"] == "user" and chat_history[i + 1]["role"] == "bot":
            prev_q = chat_history[i]["content"]
            prev_a = chat_history[i + 1]["content"]
            break

    return chat_history, prev_q, prev_a

def call_runpod_api(message, user_info):
    try:
        api_url = "https://x76r8kryd0u399-7004.proxy.runpod.net/chat"
        payload = {
            "message": message,
            "user_info": user_info
        }
        res = requests.post(api_url, json=payload, timeout=120)
        res.raise_for_status()
        data = res.json()
        return data.get("response", "⚠️ 응답이 없습니다.")
    except Exception as e:
        return f"❗ 오류 발생: {str(e)}"

# 채팅 메시지 전송
@require_POST
@csrf_exempt
def chat_send(request):
    is_guest = request.session.get('guest', False)
    user_id = request.session.get("guest_user_id") if is_guest else request.session.get("user_id")

    if not user_id:
        return redirect('user:home')

    message = request.POST.get("message", "").strip()
    if not message:
        return redirect("chat:main")

    user = User.objects.get(id=user_id)

    # ✅ 비회원 처리
    if is_guest:
        breed = request.POST.get("breed", "알 수 없음")
        chat = Chat.objects.create(dog=None, chat_title=message[:20])
        Message.objects.create(chat=chat, sender="user", message=message)

        guest_info = {
            "name": "비회원 반려견",
            "breed": breed,
            "age": "알 수 없음",
            "gender": "모름",
            "neutered": "모름",
            "disease": "모름",
            "disease_desc": "",
            "period": "모름",
            "housing": "모름",
            "chat_history": [],
            "prev_q": None,
            "prev_a": None,
            "prev_cate": None,
            "is_first_question": True
        }
        answer = call_runpod_api(message, guest_info)
        Message.objects.create(chat=chat, sender="bot", message=answer)
        return redirect('chat:chat_talk_detail', chat_id=chat.id)

    # ✅ 회원 처리
    current_dog_id = request.session.get("current_dog_id")
    dog = DogProfile.objects.filter(id=current_dog_id, user=user).first()

    if not dog:
        return JsonResponse({"error": "반려견이 선택되지 않았습니다."}, status=400)

    chat = Chat.objects.create(dog=dog, chat_title=message[:20])
    Message.objects.create(chat=chat, sender="user", message=message)

    user_info = get_dog_info(dog)
    answer = call_runpod_api(message, user_info)
    Message.objects.create(chat=chat, sender="bot", message=answer)

    return redirect('chat:chat_talk_detail', chat_id=chat.id)


# 채팅 삭제
@require_POST
@csrf_exempt
def chat_member_delete(request, chat_id):
    try:
        chat = Chat.objects.get(id=chat_id)
        user_id = request.session.get('user_id')

        if not user_id or str(chat.dog.user.id) != str(user_id):
            return JsonResponse({'status': 'unauthorized'}, status=403)

        chat.delete()
        return JsonResponse({'status': 'ok'})
    except Chat.DoesNotExist:
        return JsonResponse({'status': 'not_found'}, status=404)

# 채팅 제목 수정
@require_POST
@csrf_exempt
def chat_member_update_title(request, chat_id):
    import json
    try:
        chat = Chat.objects.get(id=chat_id)
        user_id = request.session.get('user_id')

        if not user_id or str(chat.dog.user.id) != str(user_id):
            return JsonResponse({'status': 'unauthorized'}, status=403)

        data = json.loads(request.body)
        new_title = data.get('title', '').strip()
        if new_title:
            chat.chat_title = new_title
            chat.save()
            return JsonResponse({'status': 'ok'})
        return JsonResponse({'status': 'empty_title'}, status=400)
    except Chat.DoesNotExist:
        return JsonResponse({'status': 'not_found'}, status=404)
    
def chat_guest_view(request):
    request.session.flush()
    request.session['guest'] = True

    guest_email = f"guest_{uuid.uuid4().hex[:10]}@example.com"
    guest_user = User.objects.create(email=guest_email, password='guest_pw')
    request.session['guest_user_id'] = str(guest_user.id)
    request.session['user_email'] = guest_email

    return redirect('chat:main')

# 비회원 시작용 guest 세션 생성
def chat_talk_view(request, chat_id):
    is_guest = request.session.get('guest', False)
    user_email = request.session.get("user_email")
    current_dog_id = request.session.get("current_dog_id")

    try:
        chat = Chat.objects.get(id=chat_id)
    except Chat.DoesNotExist:
        return redirect('chat:main')

    user_id = request.session.get("guest_user_id") if is_guest else request.session.get("user_id")

    # ✅ 회원의 경우 user_id 불일치 또는 user가 None이면 리다이렉트
    if not is_guest:
        if not user_id or chat.user is None or str(chat.user.id) != str(user_id):
            return redirect('chat:main')

    # ✅ 현재 강아지 ID 불일치 시 리다이렉트
    if not is_guest and chat.dog is not None and current_dog_id is not None and chat.dog.id != current_dog_id:
        return redirect('chat:main')

    # ✅ POST 요청: 메시지 전송
    if request.method == "POST":
        message = request.POST.get("message", "").strip()
        if message:
            Message.objects.create(chat=chat, sender='user', message=message)

            if is_guest:
                user_info = get_minimal_guest_info(request.session)
            else:
                chat_history, prev_q, prev_a = get_chat_history(chat)
                user_info = get_dog_info(chat.dog)
                user_info.update({
                    "chat_history": chat_history,
                    "prev_q": prev_q,
                    "prev_a": prev_a,
                    "prev_cate": None,
                    "is_first_question": len(chat_history) == 0
                })

            answer = call_runpod_api(message, user_info)
            Message.objects.create(chat=chat, sender='bot', message=answer)

        return redirect('chat:chat_talk_detail', chat_id=chat.id)

    # ✅ GET 요청: 채팅 페이지 렌더링
    messages = Message.objects.filter(chat=chat).order_by('created_at')
    chat_list = Chat.objects.filter(user=chat.user).order_by('-created_at') if chat.user else []
    now_time = timezone.localtime().strftime("%I:%M %p").lower()

    return render(request, "chat/chat_talk.html", {
        "messages": messages,
        "current_chat": chat,
        "chat_list": chat_list,
        "user_email": user_email,
        "is_guest": is_guest,
        "now_time": now_time,
    })