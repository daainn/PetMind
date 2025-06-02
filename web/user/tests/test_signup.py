import pytest
from django.urls import reverse
from user.models import User

@pytest.mark.django_db
def test_signup_with_invalid_email_format(client):
    # ✅ 유효하지 않은 이메일 형식이면 오류 발생 후 리다이렉트
    response = client.post(reverse("user:join_02"), {
        "email_id": "invalid",
        "email_domain": "bad",
        "password": "Password123!"
    })
    assert response.status_code == 302
    assert "auth_code" not in client.session


@pytest.mark.django_db
def test_signup_with_duplicate_email(client):
    # ✅ 이미 존재하는 이메일이면 오류 메시지 발생
    User.objects.create(email="exist@example.com", password="pw")
    response = client.post(reverse("user:join_02"), {
        "email_id": "exist",
        "email_domain": "example.com",
        "password": "Password123!"
    })
    assert response.status_code == 302
    assert "auth_code" not in client.session


@pytest.mark.django_db
def test_signup_with_invalid_password_format(client):
    # ✅ 비밀번호가 형식에 맞지 않으면 오류 발생
    response = client.post(reverse("user:join_02"), {
        "email_id": "new",
        "email_domain": "example.com",
        "password": "short"
    })
    assert response.status_code == 302
    assert "auth_code" not in client.session


@pytest.mark.django_db
def test_signup_success_sets_session(client):
    # ✅ 모든 조건이 충족되면 인증 코드 세션에 저장됨
    response = client.post(reverse("user:join_02"), {
        "email_id": "new",
        "email_domain": "example.com",
        "password": "Password123!"
    })
    assert response.status_code == 302
    assert "auth_code" in client.session
    assert "user_email" in client.session
    assert "user_password" in client.session


@pytest.mark.django_db
def test_email_certification_failure(client):
    # ✅ 인증번호가 틀렸을 경우 인증 실패
    session = client.session
    session["auth_code"] = "12345"
    session["user_email"] = "a@a.com"
    session["user_password"] = "pw1234pass"
    session.save()

    response = client.post(reverse("user:join_03"), {"auth_code": "99999"})
    assert "인증번호가 일치하지 않" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_email_certification_success_creates_user(client):
    # ✅ 인증번호가 일치하면 User가 생성되고 세션 초기화됨
    session = client.session
    session["auth_code"] = "54321"
    session["user_email"] = "final@pet.com"
    session["user_password"] = "Secure123!"
    session.save()

    response = client.post(reverse("user:join_03"), {"auth_code": "54321"})
    assert response.status_code == 302
    assert User.objects.filter(email="final@pet.com").exists()
    assert "user_email" not in client.session