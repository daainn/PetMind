from django import forms
from .models import DogProfile

class DogProfileForm(forms.ModelForm):
    class Meta:
        model = DogProfile
        fields = [
            'name', 'breed', 'breed_name', 'age', 'gender', 'neutered',
            'disease_history', 'living_period', 'housing_type', 'profile_image_url'
        ]
        widgets = {
            'disease_history': forms.Textarea(attrs={'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        
        age = cleaned_data.get('age')
        breed = cleaned_data.get('breed')

        if age is None or age < 0:
            self.add_error('age', '반려견 나이를 정확히 입력해주세요.')

        if not breed:
            self.add_error('breed', '반려견 품종을 선택해주세요.')

        return cleaned_data
