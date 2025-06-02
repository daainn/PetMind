import pytest
from django.urls import reverse
from user.models import User, UserInfo


@pytest.mark.django_db
def test_info_submit_creates_guest_user_and_info(client):
    data = {
        "marital_status": "법적 혼인",
        "marriage_duration": "3년",
        "divorce_status": "이혼 고려중",
        "child_status": "yes",
        "children_ages": "10세",
        "property_range": "1억원 이상",
        "experience": "가정 불화 있음",
        "detail_info": "자녀 교육 문제로 다툼이 잦습니다.",
        "marriage_skip_btn": "off",
        "children_skip_btn": "off",
        "other_skip_btn": "off",
        "detail_skip_btn": "off",
    }

    # 세션에서 guest 설정
    session = client.session
    session["guest"] = True
    session.save()

    response = client.post(reverse("dogs:dog_info_join_submit"), data)

    assert response.status_code == 302

    session = client.session
    assert "guest_info" in session
    assert session["guest_info"]["marital_status"] == "법적 혼인"



import pytest
from django.urls import reverse
from user.models import User, UserInfo

# ✅ 1. 게스트 테스트
@pytest.mark.django_db
def test_info_submit_with_skip_flags_as_guest(client):
    session = client.session
    session["guest"] = True
    session.save()

    data = {
        "marriage_skip_btn": "on",
        "children_skip_btn": "on",
        "other_skip_btn": "on",
        "detail_skip_btn": "on",
    }

    response = client.post(reverse("dogs:dog_info_join_submit"), data)
    assert response.status_code == 302

    session = client.session
    guest_info = session.get("guest_info")
    assert guest_info is not None
    assert guest_info["marital_skipped"] is True
    assert guest_info["children_skipped"] is True
    assert guest_info["other_skipped"] is True
    assert guest_info["detail_skipped"] is True


# ✅ 2. 회원 테스트
@pytest.mark.django_db
def test_info_submit_with_skip_flags_as_member(client):
    user = User.objects.create(email="member@example.com", password="pw1234")
    session = client.session
    session["user_id"] = str(user.id)
    session["user_email"] = user.email
    session["guest"] = False
    session.save()

    data = {
        "marriage_skip_btn": "on",
        "children_skip_btn": "on",
        "other_skip_btn": "on",
        "detail_skip_btn": "on",
    }

    response = client.post(reverse("dogs:dog_info_join_submit"), data)
    assert response.status_code == 302

    info = UserInfo.objects.filter(user=user).first()
    assert info is not None
    assert info.marital_skipped is True
    assert info.children_skipped is True
    assert info.other_skipped is True
    assert info.detail_skipped is True

# 로그인 후 개인정보 입력이 저장되는가?
@pytest.mark.django_db
def test_info_submit_with_authenticated_user(client):
    # 1. 회원 유저 생성
    user = User.objects.create(email="auth@example.com", password="pw1234")

    # 2. 세션에 회원 정보 설정
    session = client.session
    session["user_id"] = str(user.id)
    session["user_email"] = user.email
    session["guest"] = False
    session.save()

    # 3. POST 데이터 구성
    data = {
        "marital_status": "법적 혼인",
        "marriage_duration": "3년",
        "divorce_status": "이혼 고려중",
        "child_status": "yes",
        "has_children": True,
        "children_ages": "10세",
        "property_range": "1억원 이상",
        "experience": "가정 불화 있음",
        "detail_info": "자녀 교육 문제로 다툼이 잦습니다.",
        "marriage_skip_btn": "off",
        "children_skip_btn": "off",
        "other_skip_btn": "off",
        "detail_skip_btn": "off",
    }

    # 4. 요청
    response = client.post(reverse("dogs:dog_info_join_submit"), data)

    # 5. 결과 검증
    assert response.status_code == 302
    assert UserInfo.objects.filter(user=user).exists()

@pytest.mark.django_db
def test_info_submit_with_empty_data(client):
    # ✅ 4. 아무 값 없이 제출해도 서버 에러 없이 처리되는가?
    response = client.post(reverse("dogs:dog_info_join_submit"), {})
    # ✅ 200이 반환되고, 에러 메시지가 포함된 폼이 반환되는지 확인
    assert response.status_code == 200
    assert "form" in response.context
    form = response.context["form"]
    assert form.errors  # 폼에 에러가 존재해야 함