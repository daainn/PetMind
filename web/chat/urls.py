from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_entry, name='chat_entry'),
    path('main/', views.chat_main, name='main'),
    path('send/', views.chat_send, name='chat_send'),  # POST only

    path('guest/', views.chat_guest_view, name='chat_guest'),

    path('talk/<int:chat_id>/', views.chat_talk_view, name='chat_talk_detail'),  

    path('member/delete/<int:chat_id>/', views.chat_member_delete, name='member_chat_delete'),
    path('member/update-title/<int:chat_id>/', views.chat_member_update_title, name='member_chat_update_title'),
    path('member/chat/<int:chat_id>/', views.chat_member_start, name='chat_member_start'),
]
