from django import forms
from .models import DogProfile

class DogProfileForm(forms.ModelForm):
    profile_image = forms.ImageField(required=False)

    class Meta:
        model = DogProfile
        exclude = ['user']
        widgets = {
            'disease_history': forms.Textarea(attrs={'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        breed = cleaned_data.get('breed')

        if not name:
            self.add_error('name', '반려견 이름을 입력해주세요.')
        if not breed:
            self.add_error('breed', '반려견 품종을 선택해주세요.')

        return cleaned_data
