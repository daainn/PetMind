import pytest
import json
from django.urls import reverse
from user.models import User
from chat.models import Chat, Message

@pytest.mark.django_db
def test_chat_guest_chat_talk_view_renders_messages(client):
    # 비회원 유저 생성 및 세션 설정
    guest_user = User.objects.create(email="guest@example.com", password="pw")
    session = client.session
    session["guest"] = True
    session["guest_user_id"] = str(guest_user.id)
    session["user_email"] = guest_user.email
    session.save()

    # 채팅 및 메시지 생성
    chat = Chat.objects.create(user=guest_user, chat_title="게스트 채팅")
    Message.objects.create(chat=chat, sender="user", message="안녕하세요")

    # chat_talk_view로 접근
    response = client.get(reverse("chat:chat_talk_detail", args=[chat.id]))

    assert response.status_code == 200
    assert "안녕하세요" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_chat_member_chat_talk_view_renders_messages(client):
    # 회원 유저 생성 및 세션 설정
    user = User.objects.create(email="member@example.com", password="pw")
    session = client.session
    session["user_id"] = str(user.id)
    session["user_email"] = user.email
    session["guest"] = False
    session.save()

    # 채팅 및 메시지 생성
    chat = Chat.objects.create(user=user, chat_title="회원 채팅")
    Message.objects.create(chat=chat, sender="bot", message="환영합니다")

    # chat_talk_view로 접근
    response = client.get(reverse("chat:chat_talk_detail", args=[chat.id]))

    assert response.status_code == 200
    assert "환영합니다" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_chat_send_creates_chat_and_messages(client):
    user = User.objects.create(email="user@example.com", password="pw")
    session = client.session
    session["user_id"] = str(user.id)
    session["user_email"] = user.email
    session["guest"] = False
    session.save()

    message = "이혼 시 양육권은 어떻게 되나요?"
    response = client.post(reverse("chat:chat_send"), {
        "message": message
    })

    assert response.status_code == 302
    assert Chat.objects.filter(user=user, chat_title__startswith=message[:20]).exists()

    chat = Chat.objects.filter(user=user).first()
    msgs = Message.objects.filter(chat=chat).order_by("created_at")
    assert msgs.count() == 2
    assert msgs[0].message == message
    assert msgs[0].sender == "user"
    assert msgs[1].sender == "bot"


@pytest.mark.django_db
def test_chat_talk_view_saves_user_and_bot_message(client):
    user = User.objects.create(email="test_talk@example.com", password="pw")
    chat = Chat.objects.create(user=user, chat_title="초기 채팅")
    Message.objects.create(chat=chat, sender="user", message="기존 질문입니다.")

    session = client.session
    session["user_id"] = str(user.id)
    session["user_email"] = user.email
    session["guest"] = False
    session.save()

    # POST 요청으로 메시지 전송
    response = client.post(reverse("chat:chat_talk_detail", args=[chat.id]), {
        "message": "추가 질문입니다."
    })

    assert response.status_code == 302
    assert response.url == reverse("chat:chat_talk_detail", args=[chat.id])

    # 🔁 redirect 이후 실제 상태 확인
    response = client.get(reverse("chat:chat_talk_detail", args=[chat.id]))
    messages = Message.objects.filter(chat=chat).order_by("created_at")

    assert messages.count() == 3
    assert messages.last().message == "가상 응답입니다. 준비 중입니다."

@pytest.mark.django_db
def test_chat_member_delete_authorized_user_success(client):
    user = User.objects.create(email="delete_test@example.com", password="pw")
    chat = Chat.objects.create(user=user, chat_title="삭제용 채팅")

    session = client.session
    session["user_id"] = str(user.id)
    session["user_email"] = user.email
    session.save()

    url = reverse("chat:member_chat_delete", args=[chat.id])
    response = client.post(url)

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert not Chat.objects.filter(id=chat.id).exists()


@pytest.mark.django_db
def test_chat_member_update_title_success(client):
    user = User.objects.create(email="update_test@example.com", password="pw")
    chat = Chat.objects.create(user=user, chat_title="기존 제목")

    session = client.session
    session["user_id"] = str(user.id)
    session["user_email"] = user.email
    session.save()

    new_title = "수정된 제목"
    url = reverse("chat:member_chat_update_title", args=[chat.id])
    response = client.post(url, data=json.dumps({"title": new_title}), content_type="application/json")

    chat.refresh_from_db()
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert chat.chat_title == new_title
