import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_join_terms_service_page_renders(client):
    # ✅ 서비스 이용약관 페이지가 정상 렌더링 되는가?
    response = client.get(reverse("user:join_terms_service"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_join_terms_privacy_page_renders(client):
    # ✅ 개인정보처리방침 페이지가 정상 렌더링 되는가?
    response = client.get(reverse("user:join_terms_privacy"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_join_complete_page_renders(client):
    # ✅ 회원가입 완료 페이지가 정상 렌더링 되는가?
    response = client.get(reverse("user:join_04"))
    assert response.status_code == 200
