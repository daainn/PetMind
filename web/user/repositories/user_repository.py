from ..models import User

def get_user_by_email(email):
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return None

def user_exists_by_email(email):
    return User.objects.filter(email=email).exists()
