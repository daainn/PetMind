from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import DogProfileForm
from .models import DogProfile
from user.utils import get_or_create_user  

def dog_info_submit(request):
    if request.method == "POST":
        user, _ = get_or_create_user(request)
        is_guest = request.session.get('guest', False)

        form = DogProfileForm(request.POST)

        if form.is_valid():
            if is_guest:
                request.session['guest_dog_info'] = form.cleaned_data
                return redirect("chat:main")
            else:
                dog_profile = form.save(commit=False)
                dog_profile.user = user
                dog_profile.save()
                return redirect("chat:main")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.warning(request, f"{error}")

    else:
        form = DogProfileForm()

    return render(request, "dogs/info.html", {"form": form})
