import pytest
import uuid
from django.urls import reverse
from user.models import User

@pytest.mark.django_db
def test_chat_entry_guest_redirect(client):
    session = client.session
    session['guest'] = True
    session['guest_user_id'] = str(uuid.uuid4()) 
    session.save()

    response = client.get(reverse('chat:chat_entry'), follow=False)

    assert response.status_code == 302
    assert response.url == reverse('chat:main')


@pytest.mark.django_db
def test_chat_entry_member_redirect(client):
    user = User.objects.create(email="user@example.com", password="pw")
    session = client.session
    session['user_id'] = str(user.id)
    session['user_email'] = user.email
    session['guest'] = False
    session.save()

    response = client.get(reverse('chat:chat_entry'), follow=False)

    assert response.status_code == 302
    assert response.url == reverse('chat:main')


@pytest.mark.django_db
def test_chat_entry_unauthenticated_redirect(client):
    response = client.get(reverse('chat:chat_entry'), follow=False)

    assert response.status_code == 302
    assert response.url == reverse('user:home')
