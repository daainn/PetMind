from .models import User
import uuid

def get_or_create_user(request):
    """
    세션 기반 사용자 반환 함수.
    회원 로그인: user_id 세션에서 조회
    비회원: guest_user_id 세션에서 조회 또는 생성
    """
    user_id = request.session.get("user_id")
    if user_id:
        try:
            user = User.objects.get(id=uuid.UUID(user_id))
            return user, False
        except (User.DoesNotExist, ValueError):
            pass 
    guest_user_id = request.session.get("guest_user_id")
    if guest_user_id:
        try:
            user = User.objects.get(id=guest_user_id)
            return user, False
        except User.DoesNotExist:
            pass

    user = User.objects.create(
        email=f"guest_{uuid.uuid4().hex[:10]}@example.com",
        password="",
        is_verified=False,
        is_deleted=False,
    )
    request.session["guest_user_id"] = str(user.id)
    request.session["guest"] = True
    return user, True



def get_logged_in_user(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None