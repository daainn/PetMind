from django.test import TestCase

import uuid
from django.test import TestCase, Client
from django.urls import reverse
from user.models import User, UserInfo


class UserInfoFormTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.submit_url = reverse("dogs:dog_info_join_submit")

    def test_form_submission_creates_guest_user(self):
        # 건너뛰기 없이 모든 필드 입력
        data = {
            "marriage_status": "법적 혼인",
            "marriage_duration": "2년",
            "divorce_status": "이혼 고려중",
            "child_status": "yes",
            "child_age": "10세",
            "property_scope": "1억원 이상 ~ 10억원 미만",
            "experience": "가정 폭력 또는 정신적 고통 경험 없음",
            "detail_info": "폭력은 없지만 불화가 계속되고 있습니다."
        }

        response = self.client.post(self.submit_url, data)
        self.assertEqual(response.status_code, 302)  # redirect

        # 유저와 유저 정보 생성 여부 확인
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(UserInfo.objects.count(), 1)

        info = UserInfo.objects.first()
        self.assertEqual(info.marital_status, "법적 혼인")
        self.assertEqual(info.has_children, True)
        self.assertEqual(info.children_ages, "10세")

    def test_skipped_sections_are_stored_correctly(self):
        # 혼인, 자녀 정보만 건너뛰기 체크
        data = {
            "marriage_skip_btn": "on",
            "children_skip_btn": "on",
            "property_scope": "5천만원 미만",
            "experience": "가정 폭력 또는 정신적 고통 경험 있음",
            "detail_info": "자녀 양육비에 대한 고민이 많습니다."
        }

        response = self.client.post(self.submit_url, data)
        self.assertEqual(response.status_code, 302)

        info = UserInfo.objects.first()
        self.assertTrue(info.marital_skipped)
        self.assertTrue(info.children_skipped)
        self.assertFalse(info.other_skipped)
        self.assertFalse(info.detail_skipped)

        self.assertEqual(info.property_range, "5천만원 미만")
        self.assertIsNone(info.has_children)
        self.assertIsNone(info.marital_status)

    def test_multiple_submissions_create_multiple_users(self):
        # 두 번 제출하면 서로 다른 guest 유저 생성
        self.client.post(self.submit_url, {"marriage_status": "이혼"})
        self.client.post(self.submit_url, {"marriage_status": "법적 혼인"})

        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(UserInfo.objects.count(), 2)

    def test_required_fields_are_missing(self):
        """아무 필드 없이 제출해도 서버 에러 없이 처리"""
        response = self.client.post(self.submit_url, {})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(UserInfo.objects.count(), 1)

    def test_guest_email_format(self):
        """게스트 이메일 포맷 확인"""
        self.client.post(self.submit_url, {
            "detail_info": "게스트 이메일 확인용"
        })
        user = User.objects.first()
        self.assertTrue(user.email.startswith("guest_"))

    def test_get_request_redirects_back(self):
        """GET 요청이 오면 info 페이지로 redirect"""
        response = self.client.get(self.submit_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("dogs:dog_info_join"), response.url)

    def test_skip_all_sections(self):
        """모든 항목 건너뛰기한 경우에도 저장되는지 확인"""
        response = self.client.post(self.submit_url, {
            "marriage_skip_btn": "on",
            "children_skip_btn": "on",
            "other_skip_btn": "on",
            "detail_skip_btn": "on",
        })
        self.assertEqual(UserInfo.objects.count(), 1)
        info = UserInfo.objects.first()
        self.assertTrue(info.marital_skipped)
        self.assertTrue(info.children_skipped)
        self.assertTrue(info.other_skipped)
        self.assertTrue(info.detail_skipped)

    def test_authenticated_user_used_if_exists(self):
        """로그인한 사용자가 있을 경우 해당 user로 저장"""
        user = User.objects.create(email="test@example.com", password="pw1234")
        self.client.force_login(user)
        self.client.post(self.submit_url, {
            "marriage_status": "이혼",
        })
        info = UserInfo.objects.get(user=user)
        self.assertEqual(info.marital_status, "이혼")

    def test_duplicate_user_info_not_allowed(self):
        """같은 User에 대해 여러 UserInfo 저장 불가 (OneToOneField)"""
        user = User.objects.create(email="dup@example.com", password="pw1234")
        self.client.force_login(user)

        # 첫 번째 저장
        self.client.post(self.submit_url, {
            "marriage_status": "법적 혼인"
        })

        # 두 번째 저장 시도 → 예외 발생 예상
        with self.assertRaises(Exception):
            self.client.post(self.submit_url, {
                "marriage_status": "이혼"
            })
