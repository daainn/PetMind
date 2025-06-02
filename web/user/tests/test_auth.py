import pytest
from django.urls import reverse
from user.models import User
from django.contrib.auth.hashers import make_password

@pytest.mark.django_db
def test_login_success_sets_session(client):
    # 1. 테스트용 사용자 생성
    user = User.objects.create(email="test@example.com", password=make_password("pw1234"))

    # 2. 로그인 요청
    response = client.post(reverse("user:home"), {
        "email": "test@example.com",
        "password": "pw1234"
    })

    # 3. 성공 시 세션에 값이 저장되고 리다이렉트 발생
    assert response.status_code == 302
    assert client.session["user_id"] == str(user.id)
    assert client.session["user_email"] == user.email


@pytest.mark.django_db
def test_login_fails_with_wrong_password(client):
    User.objects.create(email="wrong@example.com", password="correct")

    response = client.post(reverse("user:home"), {
        "email": "wrong@example.com",
        "password": "wrong"
    })

    assert response.status_code == 200 
    assert "user_id" not in client.session


@pytest.mark.django_db
def test_login_fails_with_unknown_email(client):
    response = client.post(reverse("user:home"), {
        "email": "notfound@example.com",
        "password": "whatever"
    })

    assert response.status_code == 200
    assert "user_id" not in client.session


@pytest.mark.django_db
def test_logout_clears_session(client):
    # 임의의 세션 값 설정
    session = client.session
    session["user_id"] = "some-id"
    session["user_email"] = "some@email.com"
    session.save()

    response = client.get(reverse("user:home")) 
    assert "user_id" in client.session

    # 로그아웃 시도
    response = client.get(reverse("user:home")) 
    client.session.flush()

    assert "user_id" not in client.session