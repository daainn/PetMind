from django.shortcuts import render, redirect
from .forms import DogProfileForm
from user.utils import get_or_create_user
from dogs.models import DogBreed, DogProfile
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from user.models import User


def dog_info_join_view(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("user:home")  # 로그인 안 돼 있으면 홈으로

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect("user:home")

    dog_breeds = DogBreed.objects.all().order_by('name')

    if request.method == "POST":
        form = DogProfileForm(request.POST, request.FILES)

        if form.is_valid():
            dog_profile = form.save(commit=False)
            dog_profile.user = user
            ...
            dog_profile.save()
            dog = DogProfile.objects.get(pk=dog_profile.id)
            if dog:
                return redirect('chat:chat_member', dog_id=dog.id)
        else:
            print("폼 에러 발생:", form.errors)
    else:
        form = DogProfileForm()

    return render(request, "dogs/dog_info_join.html", {
        "form": form,
        "dog_breeds": dog_breeds,
    })