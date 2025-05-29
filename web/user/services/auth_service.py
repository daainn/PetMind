from ..repositories.user_repository import get_user_by_email

def authenticate_user(email, password):
    user = get_user_by_email(email)
    if user and user.password == password:
        return user
    return None
