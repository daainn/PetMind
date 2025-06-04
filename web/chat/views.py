from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.http import JsonResponse, FileResponse, HttpResponseNotAllowed, Http404, HttpResponseNotFound, HttpResponseServerError
from user.models import User
from .models import Chat, Message, Content, MessageImage, UserReview
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dogs.models import DogProfile, DogBreed
from django.contrib.auth.decorators import login_required
from user.utils import get_logged_in_user
from collections import defaultdict
from datetime import date, timedelta
import uuid
import requests
import json
from django.template.loader import render_to_string, get_template
import os
from django.conf import settings
from .report_utils.gpt_report import build_prompt, generate_response, clean_and_split
from dotenv import load_dotenv
from .report_utils.db_load import load_chat_and_profile
from .report_utils.report_pdf import generate_pdf_from_context
import time
import tempfile
from rest_framework.decorators import api_view
from rest_framework.response import Response
from chat.utils import get_image_response


def chat_entry(request):
    if request.session.get('guest'):
        return redirect('chat:main')

    elif request.session.get('user_id'):
        dog_id = request.session.get('current_dog_id')
        if dog_id:
            return redirect('chat:chat_member', dog_id=dog_id)
        else:
            return redirect('dogs:dog_info_join')

    else:
        return redirect('user:home')
    
def group_chats_by_date(chat_list):
    today = date.today()
    yesterday = today - timedelta(days=1)
    grouped = defaultdict(list)

    for chat in chat_list:
        created = chat.created_at.date()
        if created == today:
            label = "오늘"
        elif created == yesterday:
            label = "어제"
        else:
            label = created.strftime("%Y.%m.%d")
        grouped[label].append(chat)

    return dict(grouped)

def chat_member_view(request, dog_id):
    user = get_logged_in_user(request)
    if not user:
        return redirect('user:home')

    dog = get_object_or_404(DogProfile, id=dog_id, user=user)

    dog_list = DogProfile.objects.filter(user=user).order_by('created_at')

    chat_list = Chat.objects.filter(dog=dog).order_by('-created_at')
    grouped_chat_list = group_chats_by_date(chat_list)
    current_chat = Chat.objects.filter(dog=dog).order_by('-created_at').first()
    messages = Message.objects.filter(chat=current_chat).order_by('created_at') if current_chat else []

    request.session['current_dog_id'] = dog.id

    return render(request, 'chat/chat.html', {
        'grouped_chat_list': grouped_chat_list,
        'chat_list': chat_list,
        'current_chat': current_chat,
        'chat_messages': messages,
        'is_guest': False,
        'user_email': user.email,
        'dog': dog,
        'dog_list': dog_list,
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
        request.session["current_chat_id"] = str(chat.id)

        return redirect('chat:chat_talk_detail', chat_id=chat.id)

    return HttpResponseNotAllowed(['GET', 'POST'])


@require_http_methods(["GET", "POST"])
def chat_member_talk_detail(request, dog_id, chat_id):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect('user:login')

    try:
        user = User.objects.get(id=uuid.UUID(user_id))
    except (User.DoesNotExist, ValueError):
        return redirect('user:login')

    dog = get_object_or_404(DogProfile, id=dog_id, user=user)
    chat = get_object_or_404(Chat, id=chat_id, dog=dog)

    if request.method == "POST":
        message = request.POST.get("message", "").strip()
        image_files = request.FILES.getlist("images")

        if message:
            user_message = Message.objects.create(chat=chat, sender='user', message=message)
        elif image_files:
            user_message = Message.objects.create(chat=chat, sender='user', message="[이미지 전송]")
        else:
            return redirect('chat:chat_member_talk_detail', dog_id=dog.id, chat_id=chat.id)

        for img in image_files[:3]:
            try:
                MessageImage.objects.create(message=user_message, image=img)
            except Exception:
                pass

        if image_files:
            answer = get_image_response(image_files, message)
        elif message:
            user_info = get_dog_info(dog)
            answer = call_runpod_api(message, user_info)
        else:
            answer = "질문이나 이미지를 입력해주세요."

        Message.objects.create(chat=chat, sender='bot', message=answer)

        return redirect('chat:chat_member_talk_detail', dog_id=dog.id, chat_id=chat.id)

    messages = Message.objects.filter(chat=chat).prefetch_related("images").order_by('created_at')
    chat_list = Chat.objects.filter(dog=dog).order_by('-created_at')
    grouped_chat_list = group_chats_by_date(chat_list)

    dog_list = DogProfile.objects.filter(user=user).order_by('created_at')

    return render(request, "chat/chat_talk.html", {
        "messages": messages,
        "current_chat": chat,
        "chat_list": chat_list,
        "grouped_chat_list": grouped_chat_list,
        "user_email": user.email,
        "is_guest": False,
        "now_time": timezone.localtime().strftime("%I:%M %p").lower(),
        "dog": dog,
        "dog_list": dog_list,
    })


def chat_main(request):
    is_guest = request.session.get("guest", False)
    user_id = request.session.get("user_id")
    guest_user_id = request.session.get("guest_user_id")
    user_email = request.session.get("user_email")
    current_dog_id = request.session.get("current_dog_id")
    current_chat_id = request.session.get("current_chat_id")

    guest_name = request.session.get("guest_dog_name")
    guest_breed = request.session.get("guest_dog_breed")

    dog_breeds = DogBreed.objects.all().order_by("name")

    if is_guest and (not guest_name or not guest_breed):
        return render(request, "chat/chat.html", {
            "show_guest_info_form": True,
            "is_guest": True,
            "dog_breeds": dog_breeds,
        })

    chat_list, current_chat, messages = [], None, []

    if user_id and not is_guest:
        try:
            user = User.objects.get(id=user_id)
            chat_list = Chat.objects.filter(dog__user=user).order_by('-created_at')

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

            if current_chat_id:
                current_chat = Chat.objects.filter(id=current_chat_id, user=user).first()

            if not current_chat:
                current_chat = chat_list.first()

            if not current_chat:
                current_chat = Chat.objects.create(user=user, dog=None, chat_title="비회원 상담 시작")
                Message.objects.create(chat=current_chat, sender="bot", message=f"{guest_name}의 상담을 시작해볼까요? 😊")
                chat_list = Chat.objects.filter(dog=None, user=user).order_by('-created_at')

            request.session["current_chat_id"] = str(current_chat.id)

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
        'show_login_notice': is_guest 
    })

def chat_switch_dog(request, dog_id):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("user:home")

    dog = get_object_or_404(DogProfile, id=dog_id, user_id=user_id)

    return redirect('chat:chat_member', dog_id=dog.id)


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
        api_url = "http://38.128.233.224:45310/chat"
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
    image_files = request.FILES.getlist("images")

    if not message and not image_files:
        return redirect("chat:main")

    if is_guest:
        chat_id = request.session.get("current_chat_id")
        chat = Chat.objects.filter(id=chat_id, user=user).first()

        if not chat:
            chat = Chat.objects.create(user=user, dog=None, chat_title=message[:20] if message else "비회원 상담")
            request.session["current_chat_id"] = str(chat.id)

        user_message = Message.objects.create(
            chat=chat,
            sender="user",
            message=message if message else "[이미지 전송]"
        )

        for img in image_files[:3]:
            try:
                MessageImage.objects.create(message=user_message, image=img)
            except Exception:
                pass

        if image_files:
            answer = get_image_response(image_files, message)
        else:
            guest_info = {
                "name": "비회원 반려견",
                "breed": request.POST.get("breed", "알 수 없음"),
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

    chat = Chat.objects.create(
        dog=dog,
        user=user,
        chat_title=message[:20] if message else "상담 시작"
    )

    user_message = Message.objects.create(
        chat=chat,
        sender="user",
        message=message if message else "[이미지 전송]"
    )

    for img in image_files[:3]:
        try:
            MessageImage.objects.create(message=user_message, image=img)
        except Exception:
            pass

    if image_files:
        answer = get_image_response(image_files, message)
    else:
        user_info = get_dog_info(dog)
        answer = call_runpod_api(message, user_info)

    Message.objects.create(chat=chat, sender="bot", message=answer)

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
    

@require_http_methods(["GET", "POST"])
def chat_talk_view(request, chat_id):
    is_guest = request.session.get('guest', False)
    user_email = request.session.get("user_email")
    current_dog_id = request.session.get("current_dog_id")
    user_id = request.session.get("guest_user_id") if is_guest else request.session.get("user_id")

    try:
        chat = Chat.objects.get(id=chat_id)
    except Chat.DoesNotExist:
        return redirect('chat:main' if is_guest else 'chat:chat_member', dog_id=current_dog_id or 1)

    if not is_guest:
        if not user_id or not chat.user or str(chat.user.id) != str(user_id):
            return redirect('chat:chat_member', dog_id=current_dog_id or (chat.dog.id if chat.dog else 1))

    if request.method == "POST":
        message_text = request.POST.get("message", "").strip()
        image_files = request.FILES.getlist("images")

        if not message_text and not image_files:
            return redirect('chat:chat_talk_detail', chat_id=chat.id)

        user_message = Message.objects.create(
            chat=chat,
            sender='user',
            message=message_text if message_text else "[이미지 전송]"
        )

        for img in image_files[:3]:
            try:
                MessageImage.objects.create(message=user_message, image=img)
            except Exception:
                pass

        if image_files:
            answer = get_image_response(image_files, user_message)
        else:
            if is_guest:
                user_info = get_minimal_guest_info(request.session)
            else:
                user = get_object_or_404(User, id=user_id)
                chat_history, prev_q, prev_a = get_chat_history(chat)
                user_info = get_dog_info(chat.dog)
                user_info.update({
                    "chat_history": chat_history,
                    "prev_q": prev_q,
                    "prev_a": prev_a,
                    "prev_cate": None,
                    "is_first_question": len(chat_history) == 0,
                    "user_id": str(user.id)
                })

            answer = call_runpod_api(message_text, user_info)

        Message.objects.create(chat=chat, sender='bot', message=answer)
        return redirect('chat:chat_talk_detail', chat_id=chat.id)

    messages = Message.objects.filter(chat=chat).prefetch_related("images").order_by('created_at')
    chat_list = Chat.objects.filter(user__id=user_id).order_by('-created_at') if not is_guest else []
    now_time = timezone.localtime().strftime("%I:%M %p").lower()

    dog = chat.dog if not is_guest else None
    dog_list = DogProfile.objects.filter(user__id=user_id).order_by('created_at') if dog else []

    return render(request, "chat/chat_talk.html", {
        "messages": messages,
        "current_chat": chat,
        "chat_list": chat_list,
        "user_email": user_email,
        "is_guest": is_guest,
        "now_time": now_time,
        "dog": dog,
        "dog_list": dog_list
    })



def recommend_content(request, chat_id):
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({"error": "Invalid request"}, status=400)

    if request.session.get("guest", False):
        return JsonResponse({
            "error": "비회원은 추천 콘텐츠를 이용할 수 없습니다.",
            "cards_html": "",
            "has_recommendation": False
        }, status=403)

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

@csrf_exempt
def submit_review(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        chat_id = data.get('chat_id')
        score = data.get('review_score')
        review = data.get('review')

        chat = Chat.objects.get(id=chat_id)
        UserReview.objects.create(
            chat=chat,
            review_score=score,
            review=review
        )
        return JsonResponse({'status': 'ok'})

    return JsonResponse({'status': 'error'}, status=400)


@api_view(['POST'])
def generate_report(request):
    """
    1) client로부터 chat_id, start_date, end_date를 받아서
    2) 데이터베이스에서 반려견 정보와 대화 이력을 조회하고,
    3) GPT로 요약문을 생성한 뒤,
    4) generate_pdf_from_context를 호출하여 PDF를 만들고,
    5) 생성된 PDF 파일을 FileResponse로 바로 내려줍니다.
    """
    data = request.data
    print("📩 받은 데이터:", data)

    chat_id = data.get("chat_id")
    start_date = data.get("start_date")
    end_date = data.get("end_date")

    if not (chat_id and start_date and end_date):
        return Response({"error": "필수 값(chat_id, start_date, end_date)이 누락되었습니다."}, status=400)

    # 1) DB에서 반려견 프로필과 대화 이력 불러오기
    dog, history = load_chat_and_profile(chat_id)
    if not dog or not history:
        return Response({"error": "해당 chat_id에 대한 데이터가 없습니다."}, status=404)

    # 2) GPT 요약 (인트로, 조언, 다음 상담)
    messages = build_prompt(dog, history)
    raw_output = generate_response(messages)
    intro, advice, next_ = clean_and_split(raw_output)

    # 3) PDF 템플릿에 넣을 context 구성
    context = {
        "dog_name": dog["name"],
        "age": dog["age"],
        "breed_name": dog["breed_name"],
        "gender_display": dog["gender"],
        "neutered": dog["neutered"],
        "disease_history": dog["disease_history"],
        "living_period": dog["living_period"],
        "housing_type": dog["housing_type"],
        # 프로필 이미지는 절대 URL로 만들어서 HTML에서 로드할 수 있도록 합니다.
        "profile_image_url": request.build_absolute_uri("/static/images/sample_dog.jpg"),
        "start_date": start_date,
        "end_date": end_date,
        "intro_text": intro,
        "advice_text": advice,
        "next_text": next_,
        "llm_response_html": raw_output,
        # 템플릿 내에서 request를 참조해야 할 경우를 대비해 전달합니다.
        "request": request,
    }

    # 4) generate_pdf_from_context 호출 → 임시 파일 경로 리턴
    try:
        # pdf_filename 파라미터로 원하는 파일명을 넘겨줄 수 있습니다(생략 시 "report.pdf").
        # 여기서는 chat_id 기반으로 파일명을 지정해 보겠습니다.
        pdf_temp_path = generate_pdf_from_context(context, pdf_filename=f"report_{chat_id}.pdf")
        # pdf_temp_path: 예) "/tmp/tmpabcd1234.pdf"
        # (generate_pdf_from_context 내부에서 NamedTemporaryFile, mkstemp을 썼으므로 시스템 임시 디렉터리에 저장됨)
    except Exception as e:
        # PDF 생성 중 에러가 발생하면 500으로 응답
        return Response({"error": f"PDF 생성 실패: {str(e)}"}, status=500)

    # 5) FileResponse로 생성된 PDF를 클라이언트로 바로 스트리밍
    if os.path.exists(pdf_temp_path):
        try:
            # 'rb' 모드로 열어서 FileResponse로 반환
            pdf_file = open(pdf_temp_path, 'rb')
            response = FileResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="report_{chat_id}.pdf"'

            # 뷰가 끝날 때 임시 파일을 삭제하도록 합니다.
            # FileResponse가 닫힐 때까지 기다렸다가 삭제하기 위해 아래와 같이 하거나,
            # 실제 서비스에서는 celery 같은 작업 큐를 써서 별도 cleanup 작업을 돌려도 좋습니다.
            def remove_temp_file(response):
                try:
                    pdf_file.close()
                    os.remove(pdf_temp_path)
                except Exception:
                    pass

            response.call_on_close(remove_temp_file)
            return response

        except Exception as e:
            # 파일 읽기/스트리밍 중 에러
            return HttpResponseServerError(f"PDF 파일 전송 중 에러: {str(e)}")
    else:
        return HttpResponseNotFound("생성된 PDF 파일을 찾을 수 없습니다.")

def download_report(request, chat_id):
    dog, history = load_chat_and_profile(chat_id)
    if not dog or not history:
        raise Http404("상담 이력 또는 반려견 정보가 없습니다.")

    messages = build_prompt(dog, history)
    raw_output = generate_response(messages)
    intro, advice, next_ = clean_and_split(raw_output)

    context = {
        "dog_name": dog["name"],
        "age": dog["age"],
        "breed_name": dog["breed_name"],
        "gender_display": dog["gender"],
        "neutered": dog["neutered"],
        "disease_history": dog["disease_history"],
        "living_period": dog["living_period"],
        "housing_type": dog["housing_type"],
        "profile_image_url": "file://" + os.path.join(settings.BASE_DIR, "static/images/sample_dog.jpg"),
        "start_date": "2025-06-01",
        "end_date": "2025-06-07",
        "intro_text": intro,
        "advice_text": advice,
        "next_text": next_,
        "llm_response_html": raw_output,
        "request": request,
    }

    pdf_path = generate_pdf_from_context(context)

    try:
        with open(pdf_path, "rb") as f:
            response = FileResponse(f, as_attachment=True, filename="상담리포트.pdf")
            return response
    finally:
        try:
            os.remove(pdf_path)
        except Exception:
            pass

@api_view(['GET'])
def check_report_status(request):
    # 테스트용: 항상 완료 상태 반환
    return Response({"status": "done"})

# def download_report_pdf(request, chat_id):
#     file_path = os.path.join(settings.MEDIA_ROOT, f"report_{chat_id}.pdf")
#     if not os.path.exists(file_path):
#         raise Http404("PDF 파일이 존재하지 않습니다.")
#     return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=f"report_{chat_id}.pdf")