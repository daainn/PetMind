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
        return redirect("user:home")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect("user:home")

    dog_breeds = DogBreed.objects.all().order_by('name')
    is_add_mode = request.GET.get("mode") == "add"

    if request.method == "POST":
        form = DogProfileForm(request.POST, request.FILES)

        if form.is_valid():
            dog_profile = form.save(commit=False)
            dog_profile.user = user
            dog_profile.save()

            return redirect('chat:chat_member', dog_id=dog_profile.id)
        else:
            print("폼 에러 발생:", form.errors)
    else:
        form = DogProfileForm()

    return render(request, "dogs/dog_info_join.html", {
        "form": form,
        "dog_breeds": dog_breeds,
        "is_add_mode": is_add_mode
    })
