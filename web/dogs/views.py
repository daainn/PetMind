from django.shortcuts import render, redirect, get_object_or_404
from .forms import DogProfileForm
from user.utils import get_or_create_user
from dogs.models import DogBreed, DogProfile
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from user.utils import get_logged_in_user
from dogs.utils import get_test_questions
import os
from user.models import User
from collections import Counter
from django.views.decorators.http import require_POST
from dogs.models import PersonalityResult
from dogs.utils import generate_character_from_type
from typing import List
from django.urls import reverse
import asyncio
from asgiref.sync import async_to_sync
from django.http import JsonResponse


def dog_info_join_view(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("user:home")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect("user:home")

    dog_breeds = DogBreed.objects.all().order_by('name')

    mode = request.GET.get("mode", "add")
    is_add_mode = mode == "add"
    edit_dog_id = request.GET.get("dog_id")

    dog_instance = None
    if not is_add_mode and edit_dog_id:
        dog_instance = get_object_or_404(DogProfile, id=edit_dog_id, user=user)

    if request.method == "POST":
        form = DogProfileForm(request.POST, request.FILES, instance=dog_instance)

        if form.is_valid():
            dog_profile = form.save(commit=False)
            dog_profile.user = user

            if not request.FILES.get('profile_image') and dog_instance:
                dog_profile.profile_image = dog_instance.profile_image

            dog_profile.save()

            return redirect('chat:chat_member', dog_id=dog_profile.id)
        else:
            print("폼 에러 발생:", form.errors)

    else:
        form = DogProfileForm(instance=dog_instance)

    return render(request, "dogs/dog_info_join.html", {
        "form": form,
        "dog_breeds": dog_breeds,
        "is_add_mode": is_add_mode,
        "edit_dog_id": edit_dog_id,
        "dog_instance": dog_instance,
    })

    
@require_POST
def delete_dog_profile(request, dog_id):

    user = get_logged_in_user(request)
    if not user:
        return redirect('user:home')

    try:
        dog = DogProfile.objects.get(id=dog_id, user=user)
    except DogProfile.DoesNotExist:
        return redirect('user:home')

    all_dogs = DogProfile.objects.filter(user=user).order_by('created_at')
    total_dog_count = all_dogs.count()

    dog.delete()

    if total_dog_count == 1:
        return redirect('/dogs/dog_info/join/?mode=add')
    else:
        latest_dog = DogProfile.objects.filter(user=user).order_by('created_at').last()
        return redirect('chat:chat_member', dog_id=latest_dog.id)


async def get_all_test_questions() -> List[dict]:
    all_questions = []
    for test_id in range(1, 13):
        questions = await get_test_questions(test_id)
        all_questions.extend(questions)
    return all_questions


def dog_personality_test_view(request, dog_id):
    user = get_logged_in_user(request)
    if not user:
        return redirect('user:home')

    dog_list = DogProfile.objects.filter(user=user).order_by('created_at')
    current_dog = get_object_or_404(DogProfile, id=dog_id, user=user)

    return render(request, 'dogs/dog_personality_test.html', {
        'hide_report_button': True,
        'is_guest': False,
        'dog': current_dog,
        'dog_id': current_dog.id,
        'dog_list': dog_list,
        'user_email': user.email,
    })

def get_test_questions_api(request, dog_id):
    questions = asyncio.run(get_all_test_questions())
    return JsonResponse({'questions': questions})

def submit_personality_test(request, dog_id):
    if request.method == 'POST':
        answers = request.POST
        counter = Counter()

        for key in answers:
            val = answers.get(key)
            if val in ['E', 'I', 'S', 'N', 'T', 'F', 'J', 'P']:
                counter[val] += 1

        mbti = (
            ('E' if counter['E'] >= counter['I'] else 'I') +
            ('S' if counter['S'] >= counter['N'] else 'N') +
            ('T' if counter['T'] >= counter['F'] else 'F') +
            ('J' if counter['J'] >= counter['P'] else 'P')
        )

        result = async_to_sync(generate_character_from_type)(mbti)

        PersonalityResult.objects.update_or_create(
            dog_id=dog_id,
            defaults={
                'type': result["type"],
                'character': result["character"],
                'hashtags': result.get("hashtags", [])
            }
        )

        return redirect(reverse('dogs:dog_personality_result', args=[dog_id]))

    return redirect('dogs:dog_personality_test', dog_id=dog_id)


def dog_personality_result_view(request, dog_id):
    user = get_logged_in_user(request)
    if not user:
        return redirect('user:home')

    dog_list = DogProfile.objects.filter(user=user).order_by('created_at')
    current_dog = get_object_or_404(DogProfile, id=dog_id, user=user)

    result = get_object_or_404(PersonalityResult, dog_id=dog_id)

    return render(request, 'dogs/dog_personality_result.html', {
        'hide_report_button': True,
        'is_guest': False,
        'dog': current_dog,
        'dog_id': current_dog.id,
        'dog_list': dog_list,
        'user_email': user.email,
        "type": result.type,
        "character": result.character,
        "hashtags": result.hashtags if hasattr(result, 'hashtags') else [],
    })