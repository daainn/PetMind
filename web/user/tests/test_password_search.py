import pytest
from django.urls import reverse
from user.models import User

@pytest.mark.django_db
def test_find_password_with_unknown_email(client):
    # ✅ 존재하지 않는 이메일로 요청하면 에러 메시지 발생 & same page 렌더링
    response = client.post(reverse("user:find_password"), {"email": "notfound@example.com"})
    assert response.status_code == 200
    assert "reset_email" not in client.session


@pytest.mark.django_db
def test_find_password_with_valid_email_sets_session(client):
    # ✅ 존재하는 이메일일 경우 세션에 저장되고 redirect
    user = User.objects.create(email="found@example.com", password="pw1234")
    response = client.post(reverse("user:find_password"), {"email": "found@example.com"})
    assert response.status_code == 302
    assert client.session["reset_email"] == "found@example.com"


@pytest.mark.django_db
def test_find_password_complete_uses_session_data(client):
    # ✅ find_password_complete는 세션에 있는 이메일을 기준으로 유저 정보를 전달
    user = User.objects.create(email="resetme@example.com", password="pw1234")
    session = client.session
    session["reset_email"] = "resetme@example.com"
    session.save()

    response = client.get(reverse("user:find_password_complete"))
    assert response.status_code == 200
    assert b"pw1234" in response.content
