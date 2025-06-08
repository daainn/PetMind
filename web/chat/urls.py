from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_entry, name='chat_entry'),

    path('main/', views.chat_main, name='main'),
    path('guest/register/', views.guest_profile_register, name='guest_profile_register'),

    path('<int:dog_id>/', views.chat_member_view, name='chat_member'),
    path('<int:dog_id>/talk/<int:chat_id>/', views.chat_member_talk_detail, name='chat_member_talk_detail'),
    path('<int:dog_id>/delete/<int:chat_id>/', views.chat_member_delete, name='chat_member_delete'),
    path('<int:dog_id>/update-title/<int:chat_id>/', views.chat_member_update_title, name='chat_member_update_title'),
    path('api/review/submit/', views.submit_review, name='submit_review'),
    path("report/generate/", views.generate_report, name='generate_report'),
    path('chat/<int:chat_id>/report-feedback/', views.chat_report_feedback_view, name='chat_report_feedback'),
    path('report/pdf/<int:chat_id>/', views.download_report_pdf, name='download_report_pdf'),
    path('report/status/', views.check_report_status, name='check_report_status'),
    path('<int:dog_id>/switch/', views.chat_switch_dog, name='chat_switch_dog'),

    path('send/', views.chat_send, name='chat_send'),
    path('talk/<int:chat_id>/', views.chat_talk_view, name='chat_talk_detail'),
    path('recommend/<int:chat_id>/', views.recommend_content, name='recommend_content'),
   
]

