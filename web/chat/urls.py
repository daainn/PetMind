from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_entry, name='chat_entry'),

    # ✅ 비회원 URL 정리
    path('main/', views.chat_main, name='main'),
    path('guest/register/', views.guest_profile_register, name='guest_profile_register'),

    # 회원
    path('<int:dog_id>/', views.chat_member_view, name='chat_member'),
    path('<int:dog_id>/talk/<int:chat_id>/', views.chat_member_talk_detail, name='chat_member_talk_detail'),
    path('<int:dog_id>/delete/<int:chat_id>/', views.chat_member_delete, name='chat_member_delete'),
    path('<int:dog_id>/update-title/<int:chat_id>/', views.chat_member_update_title, name='chat_member_update_title'),

    # 공통 전송 및 추천
    path('send/', views.chat_send, name='chat_send'),
    path('talk/<int:chat_id>/', views.chat_talk_view, name='chat_talk_detail'),
    path('recommend/<int:chat_id>/', views.recommend_content, name='recommend_content'),
]
