from .models import User
import uuid

def get_or_create_user(request):
    """
    로그인한 회원이면 그대로 return,
    비회원이면 세션 기반 UUID를 이용해 가상의 유저 생성
    """
    if request.user.is_authenticated:
        return request.user, False  # False → 새로 만든 게 아님

    # 세션에 가상 유저 ID가 있는지 확인
    guest_user_id = request.session.get("guest_user_id")

    if guest_user_id:
        try:
            user = User.objects.get(id=guest_user_id)
            return user, False
        except User.DoesNotExist:
            pass

    # 없으면 새로 생성 (DB에 저장)
    user = User.objects.create(
        email=f"guest_{uuid.uuid4().hex[:10]}@example.com",
        password="",  # 실제 로그인은 못함
        is_verified=False,
        is_deleted=False,
    )
    request.session["guest_user_id"] = str(user.id)
    request.session["guest"] = True
    return user, True  # True → 새로 만든 유저임
