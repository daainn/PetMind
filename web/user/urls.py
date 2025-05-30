from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
app_name = 'user'

urlpatterns = [
    path('', views.home, name='home'),
    path('password/', views.find_password, name='find_password'),
    path('password/complete/', views.find_password_complete, name='find_password_complete'),
    path('login/', auth_views.LoginView.as_view(template_name='user/login.html'), name='login'),

    path('logout/', views.logout_view, name='logout'),

    path('chat/guest/', views.chat_guest_view, name='chat_guest'),

    path('info/', views.info, name='info'),
    path('info/cancel', views.info_cancel, name='info_cancel'), 

    path('join/', views.join_user_form, name='join_01'),
    path('join/popup_service', views.join_terms_service, name='join_terms_service'),
    path('join/popup_privacy', views.join_terms_privacy, name='join_terms_privacy'),
    path('join/email', views.join_user_email_form, name='join_02'),
    path('join/email/send-auth-code/', views.send_auth_code, name='send_auth_code'),
    path('join/email/verify-auth-code/', views.verify_auth_code, name='verify_auth_code'),

    path('join/complete/', views.join_user_complete, name='join_complete')

]
