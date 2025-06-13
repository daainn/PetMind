# dogs/urls.py
from django.urls import path
from . import views

app_name = 'dogs'

urlpatterns = [
    path('dog_info/join/', views.dog_info_join_view, name='dog_info_join'),
    path('delete/<int:dog_id>/', views.delete_dog_profile, name='delete_dog_profile'),
    path('personality-test/<int:dog_id>/', views.dog_personality_test_view, name='dog_personality_test'),
    path('personality-test/api/<int:dog_id>/', views.get_test_questions_api, name='get_test_questions_api'),
    path('personality-test/<int:dog_id>/submit/', views.submit_personality_test, name='submit_personality_test'),
    path('personality-test/<int:dog_id>/result/', views.dog_personality_result_view, name='dog_personality_result'),
]
