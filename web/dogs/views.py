from django.shortcuts import render, redirect
from .forms import DogProfileForm
from user.utils import get_or_create_user  
from dogs.models import DogBreed, DogProfile
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os


def dog_info_join_view(request):
    user, _ = get_or_create_user(request)
    if not user:
        return redirect('user:home')

    dog_breeds = DogBreed.objects.all().order_by('name')

    if request.method == "POST":
        form = DogProfileForm(request.POST, request.FILES)

        if form.is_valid():
            dog_profile = form.save(commit=False)  
            dog_profile.user = user 

            # 견종 처리
            breed_id = form.cleaned_data.get('breed').id if form.cleaned_data.get('breed') else None
            breed_obj = DogBreed.objects.filter(id=breed_id).first()

            if not breed_obj:
                form.add_error('breed', "올바른 견종을 선택해주세요.")
            else:
                dog_profile.breed = breed_obj

                # 프로필 이미지 저장
                profile_image = request.FILES.get("profile_image")
                if profile_image:
                    path = default_storage.save(f"profile_images/{profile_image.name}", ContentFile(profile_image.read()))
                    dog_profile.profile_image_url = os.path.join(settings.MEDIA_URL, path)

                dog_profile.save()
                return redirect("chat:main")
        else:
            print("폼 에러 발생:", form.errors)

    else:
        form = DogProfileForm()

    return render(request, "dogs/dog_info_join.html", {
        "form": form,
        "dog_breeds": dog_breeds,
    })
