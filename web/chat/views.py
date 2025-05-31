from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from user.models import User
from .models import Chat, Message, Content, MessageImage
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dogs.models import DogProfile, DogBreed
from django.http import HttpResponseNotAllowed
from django.views.decorators.http import require_http_methods

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
    
def chat_member_view(request, dog_id):
    if not request.user.is_authenticated:
        return redirect('user:login')

    dog = get_object_or_404(DogProfile, id=dog_id, user=request.user)
    chat_list = Chat.objects.filter(dog__user=request.user).order_by('-created_at')
    current_chat = Chat.objects.filter(dog=dog).order_by('-created_at').first()
    messages = Message.objects.filter(chat=current_chat).order_by('created_at') if current_chat else []

    return render(request, 'chat/chat.html', {
        'chat_list': chat_list,
        'current_chat': current_chat,
        'chat_messages': messages,
        'is_guest': False,
        'user_email': request.user.email,
        'dog': dog,
    })

@csrf_exempt
@require_http_methods(["GET", "POST"])
def guest_profile_register(request):
    if request.method == 'GET':
        request.session.flush()
        request.session['guest'] = True

        guest_email = f"guest_{uuid.uuid4().hex[:10]}@example.com"
        guest_user = User.objects.create(email=guest_email, password='guest_pw')
        request.session['guest_user_id'] = str(guest_user.id)
        request.session['user_email'] = guest_email

        return redirect('chat:main')

    elif request.method == 'POST':
        guest_name = request.POST.get("guest_name", "").strip()
        guest_breed = request.POST.get("guest_breed", "").strip()

        if not guest_name or not guest_breed:
            return redirect('chat:main')

        request.session["guest_dog_name"] = guest_name
        request.session["guest_dog_breed"] = guest_breed

        guest_user_id = request.session.get("guest_user_id")
        user = User.objects.get(id=guest_user_id)

        chat = Chat.objects.create(user=user, dog=None, chat_title="비회원 상담 시작")
        welcome_message = f"{guest_name}의 상담을 시작해볼까요? 😊"
        Message.objects.create(chat=chat, sender="bot", message=welcome_message)

        return redirect('chat:chat_talk_detail', chat_id=chat.id)

    return HttpResponseNotAllowed(['GET', 'POST'])

def chat_member_talk_detail(request, dog_id, chat_id):
    if not request.user.is_authenticated:
        return redirect('user:login')

    dog = get_object_or_404(DogProfile, id=dog_id, user=request.user)
    chat = get_object_or_404(Chat, id=chat_id, dog=dog)

    if request.method == "POST":
        message = request.POST.get("message", "").strip()
        if message:
            Message.objects.create(chat=chat, sender='user', message=message)

            user_info = get_dog_info(request.user)
            answer = call_runpod_api(message, user_info)
            Message.objects.create(chat=chat, sender='bot', message=answer)

        return redirect('chat:chat_member_talk_detail', dog_id=dog.id, chat_id=chat.id)

    messages = Message.objects.filter(chat=chat).order_by('created_at')
    chat_list = Chat.objects.filter(dog__user=request.user).order_by('-created_at')
    now_time = timezone.localtime().strftime("%I:%M %p").lower()

    return render(request, "chat/chat_talk.html", {
        "messages": messages,
        "current_chat": chat,
        "chat_list": chat_list,
        "user_email": request.user.email,
        "is_guest": False,
        "now_time": now_time,
        "dog": dog,
    })




# 메인 채팅 페이지
def chat_main(request):
    is_guest = request.session.get("guest", False)
    user_id = request.session.get("user_id")
    guest_user_id = request.session.get("guest_user_id")
    user_email = request.session.get("user_email")
    current_dog_id = request.session.get("current_dog_id")

    # ✅ 비회원 기본 정보
    guest_name = request.session.get("guest_dog_name")
    guest_breed = request.session.get("guest_dog_breed")

    # ✅ 견종 리스트: 비회원 이름/견종 입력 폼용
    dog_breeds = DogBreed.objects.all().order_by("name")

    # ✅ 비회원인데 이름이나 견종이 없으면 폼 먼저 보여주기
    if is_guest and (not guest_name or not guest_breed):
        return render(request, "chat/chat.html", {
            "show_guest_info_form": True,
            "is_guest": True,
            "dog_breeds": dog_breeds,
        })

    # ✅ 채팅 데이터 초기화
    chat_list, current_chat, messages = [], None, []

    if user_id and not is_guest:
        try:
            user = User.objects.get(id=user_id)
            chat_list = Chat.objects.filter(dog__user=user).order_by('-created_at')

            # ✅ 최근 채팅으로 설정
            if current_dog_id:
                current_chat = Chat.objects.filter(dog__id=current_dog_id).first()
            else:
                current_chat = chat_list.first()
                if current_chat and current_chat.dog:
                    request.session["current_dog_id"] = current_chat.dog.id

        except User.DoesNotExist:
            return redirect('user:home')

    elif is_guest and guest_user_id:
        try:
            user = User.objects.get(id=guest_user_id)
            chat_list = Chat.objects.filter(dog=None, user=user).order_by('-created_at')

            # ✅ 새로 만든 채팅이 있다면 우선 표시
            new_chat_id = request.session.pop("new_chat_id", None)
            if new_chat_id:
                current_chat = Chat.objects.filter(id=new_chat_id, user=user).first()
            else:
                current_chat = chat_list.first()

        except User.DoesNotExist:
            return redirect('user:home')

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
        'guest_dog_name': guest_name,
        'guest_dog_breed': guest_breed,
        'dog_breeds': dog_breeds,
        'show_guest_info_form': False,
        'show_login_notice': is_guest  # ✅ 비회원 로그인 유도 문구용
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
    name = session.get("guest_dog_name", "비회원견")
    breed = session.get("guest_dog_breed", "견종 정보 없음")
    return {
        "name": name,
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

@require_POST
@csrf_exempt
def chat_send(request):
    is_guest = request.session.get('guest', False)
    user_id = request.session.get("guest_user_id") if is_guest else request.session.get("user_id")
    if not user_id:
        return redirect('user:home')

    user = get_object_or_404(User, id=user_id)
    message = request.POST.get("message", "").strip()
    if not message:
        return redirect("chat:main")

    user = User.objects.get(id=user_id)

    if is_guest:
        breed = request.POST.get("breed", "알 수 없음")
        chat = Chat.objects.create(dog=None, chat_title=message[:20])
        user_message = Message.objects.create(chat=chat, sender="user", message=message)

        image_files = request.FILES.getlist("images")
        for idx, img in enumerate(image_files[:3]):
            try:
                MessageImage.objects.create(message=user_message, image=img)
            except Exception as e:
                pass

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

    current_dog_id = request.session.get("current_dog_id")
    dog = DogProfile.objects.filter(id=current_dog_id, user=user).first()

    if not dog:
        return JsonResponse({"error": "반려견이 선택되지 않았습니다."}, status=400)

    chat = Chat.objects.create(dog=dog, chat_title=message[:20])
    user_message = Message.objects.create(chat=chat, sender="user", message=message)

    image_files = request.FILES.getlist("images")
    for idx, img in enumerate(image_files[:3]):
        try:
            MessageImage.objects.create(message=user_message, image=img)
        except Exception as e:
            pass

    user_info = get_dog_info(dog)
    answer = call_runpod_api(message, user_info)
    Message.objects.create(chat=chat, sender="bot", message=answer)

    if is_guest:
        return redirect('chat:chat_talk_detail', chat_id=chat.id)
    else:
        return redirect('chat:chat_member_talk_detail', dog_id=dog.id, chat_id=chat.id)


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
    
def chat_talk_view(request, chat_id):
    is_guest = request.session.get('guest', False)
    user_email = request.session.get("user_email")
    current_dog_id = request.session.get("current_dog_id")

    try:
        chat = Chat.objects.get(id=chat_id)
    except Chat.DoesNotExist:
        return redirect('chat:main')

    user_id = request.session.get("guest_user_id") if is_guest else request.session.get("user_id")

    if not is_guest:
        if not user_id or chat.user is None or str(chat.user.id) != str(user_id):
            return redirect('chat:main')

    if not is_guest and chat.dog is not None and current_dog_id is not None and chat.dog.id != current_dog_id:
        return redirect('chat:main')

    if request.method == "POST":
        message_text = request.POST.get("message", "").strip()

        if message_text:
            user_message = Message.objects.create(chat=chat, sender='user', message=message_text)

            image_files = request.FILES.getlist("images")
            for img in image_files[:3]:
                try:
                    MessageImage.objects.create(message=user_message, image=img)
                except Exception:
                    pass

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

            answer = call_runpod_api(message_text, user_info)
            Message.objects.create(chat=chat, sender='bot', message=answer)

        return redirect('chat:chat_talk_detail', chat_id=chat.id)

    messages = Message.objects.filter(chat=chat).prefetch_related("images").order_by('created_at')
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



def recommend_content(request, chat_id):
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({"error": "Invalid request"}, status=400)

    chat = Chat.objects.get(id=chat_id)
    history = Message.objects.filter(chat=chat).order_by("created_at")
    chat_history = [
        {"role": "user" if m.sender == "user" else "assistant", "content": m.message}
        for m in history
    ]

    contents = Content.objects.all().values("title", "body", "reference_url", "image_url")
    df = pd.DataFrame.from_records(contents)

    if df.empty:
        return JsonResponse({
            "cards_html": "",
            "has_recommendation": False
        })

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(df["body"])
    chat_text = "\n".join([m["content"] for m in chat_history if m["role"] in ["user", "assistant"]])

    if not chat_text.strip():
        return JsonResponse({
            "cards_html": "",
            "has_recommendation": False
        })

    user_vector = vectorizer.transform([chat_text])
    cosine_scores = cosine_similarity(user_vector, tfidf_matrix).flatten()
    top_indices = cosine_scores.argsort()[-3:][::-1]
    top_contents = df.iloc[top_indices]

    # ✅ 미니 카드 형식으로 HTML 구성
    html = '''
    <div style="padding: 10px 16px;">
    <p style="font-weight:600; margin: 0 0 12px 0; font-size:15px;">
    🐾 반려견의 마음을 이해하는 데 도움 되는 이야기들이에요:
    </p>
    <div style="display:flex; flex-direction:column; gap:12px;">
    '''
    for item in top_contents.to_dict(orient="records"):
        html += f'''
        <a href="{item['reference_url']}" target="_blank" style="text-decoration:none; color:inherit;">
        <div style="border:1px solid #eee; border-radius:10px; padding:12px 16px; background:#fff; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
            <p style="font-size:14px; font-weight:600; margin:0 0 4px;">{item['title']}</p>
            <p style="font-size:13px; color:#555; margin:0; line-height:1.4;">{item['body'][:80]}...</p>
        </div>
        </a>
        '''
    html += '</div></div>'

    # ✅ Message로 저장
    Message.objects.create(
        chat=chat,
        sender="bot",
        message=html,
        created_at=timezone.now()
    )

    return JsonResponse({
        "cards_html": html,
        "has_recommendation": True
    })