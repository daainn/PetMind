from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # 공통 진입
    path('', views.chat_entry, name='chat_entry'),

    # 비회원
    path('guest/', views.chat_guest_view, name='chat_guest'),
    path('main/', views.chat_main, name='main'),  # name 꼭 맞춰야 함

    # 회원
    path('<int:dog_id>/', views.chat_member_view, name='chat_member'),
    path('<int:dog_id>/talk/<int:chat_id>/', views.chat_member_talk_detail, name='chat_member_talk_detail'),
    path('<int:dog_id>/delete/<int:chat_id>/', views.chat_member_delete, name='chat_member_delete'),
    path('<int:dog_id>/update-title/<int:chat_id>/', views.chat_member_update_title, name='chat_member_update_title'),

    # 공통 전송
    path('send/', views.chat_send, name='chat_send'),
]
