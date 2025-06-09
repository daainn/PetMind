from django.shortcuts import render, redirect, get_object_or_404
from .forms import DogProfileForm
from user.utils import get_or_create_user
from dogs.models import DogBreed, DogProfile
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from user.utils import get_logged_in_user
import os
from user.models import User
from django.views.decorators.http import require_POST


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
    # 기존 코드 : 삭제 직후 기준으로 dog 개수를 확인함
    # 따라서 => (삭제가 프로필 추가 페이지 존재하기 때문에 등록인지, 수정인지 구분 못 함)
    # 수정 코드 : 삭제 이전 dog 개수 확인

    user = get_logged_in_user(request)  # 유저 정보 확인
    if not user:    # 로그인 안되는 경우
        return redirect('user:home')
    
    # 삭제할 반려견 아이디 찾음
    try:
        dog = DogProfile.objects.get(id=dog_id, user=user)
    except DogProfile.DoesNotExist:
        return redirect('user:home')
    
    # 삭제 전 반려견 리스트 확인
    all_dogs = DogProfile.objects.filter(user=user).order_by('created_at')
    total_dog_count = all_dogs.count()  # 반려견 수 확인

    dog.delete()  # 삭제 처리

    if total_dog_count == 1:
        # 마지막 한 마리를 삭제한 경우
        return redirect('/dogs/join/?mode=add')
    else:
        # 여러 마리 중 하나만 삭제한 경우
        latest_dog = DogProfile.objects.filter(user=user).order_by('created_at').last()
        return redirect('chat:chat_member', dog_id=latest_dog.id)
